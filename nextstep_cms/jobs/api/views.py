from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from ..models import (
    Company, JobPosting, ProcessedJob, JobAlert, SavedJob, JobMatch
)
from profiles.models import UserProfile
from .serializers import (
    CompanySerializer, JobPostingSerializer, JobAlertSerializer,
    SavedJobSerializer, JobMatchSerializer, JobSearchSerializer,
    ScrapeJobsSerializer
)
from ..tasks import scrape_jobs_from_sources


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    
    def get_queryset(self):
        queryset = Company.objects.all()
        search = self.request.query_params.get('search', None)
        industry = self.request.query_params.get('industry', None)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        if industry:
            queryset = queryset.filter(industry__icontains=industry)
            
        return queryset.order_by('name')


class JobPostingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = JobPosting.objects.filter(is_active=True)
    serializer_class = JobPostingSerializer
    
    def get_queryset(self):
        queryset = JobPosting.objects.filter(is_active=True, is_processed=True)
        
        # Basic filters
        location = self.request.query_params.get('location')
        job_type = self.request.query_params.get('job_type')
        experience_level = self.request.query_params.get('experience_level')
        remote_only = self.request.query_params.get('remote_only')
        
        if location:
            queryset = queryset.filter(location__icontains=location)
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)
        if remote_only == 'true':
            queryset = queryset.filter(remote_friendly=True)
            
        return queryset.order_by('-posted_date', '-quality_score')


class JobAlertViewSet(viewsets.ModelViewSet):
    serializer_class = JobAlertSerializer
    
    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if user_id:
            return JobAlert.objects.filter(user_profile_id=user_id)
        return JobAlert.objects.none()
    
    def perform_create(self, serializer):
        user_id = self.request.data.get('user_id')
        if user_id:
            user_profile = get_object_or_404(UserProfile, id=user_id)
            serializer.save(user_profile=user_profile)


class SavedJobViewSet(viewsets.ModelViewSet):
    serializer_class = SavedJobSerializer
    
    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        if user_id:
            return SavedJob.objects.filter(user_profile_id=user_id)
        return SavedJob.objects.none()
    
    def perform_create(self, serializer):
        user_id = self.request.data.get('user_id')
        if user_id:
            user_profile = get_object_or_404(UserProfile, id=user_id)
            serializer.save(user_profile=user_profile)


class JobSearchView(APIView):
    """Advanced job search with filters"""
    
    def post(self, request):
        serializer = JobSearchSerializer(data=request.data)
        if serializer.is_valid():
            filters = serializer.validated_data
            
            # Build query
            queryset = JobPosting.objects.filter(
                is_active=True, 
                is_processed=True
            ).select_related('company', 'processed_data')
            
            # Apply filters
            if filters.get('keywords'):
                q_objects = Q()
                for keyword in filters['keywords']:
                    q_objects |= (
                        Q(title__icontains=keyword) |
                        Q(description__icontains=keyword) |
                        Q(processed_data__keywords__contains=[keyword])
                    )
                queryset = queryset.filter(q_objects)
            
            if filters.get('location'):
                queryset = queryset.filter(location__icontains=filters['location'])
            
            if filters.get('remote_only'):
                queryset = queryset.filter(remote_friendly=True)
            
            if filters.get('job_type'):
                queryset = queryset.filter(job_type=filters['job_type'])
            
            if filters.get('experience_level'):
                queryset = queryset.filter(experience_level=filters['experience_level'])
            
            if filters.get('industry'):
                queryset = queryset.filter(
                    Q(company__industry__icontains=filters['industry']) |
                    Q(processed_data__ai_industry_category__icontains=filters['industry'])
                )
            
            if filters.get('company'):
                queryset = queryset.filter(company__name__icontains=filters['company'])
            
            # Salary filters
            if filters.get('min_salary'):
                queryset = queryset.filter(
                    Q(salary_min__gte=filters['min_salary']) |
                    Q(salary_max__gte=filters['min_salary'])
                )
            
            if filters.get('max_salary'):
                queryset = queryset.filter(
                    Q(salary_max__lte=filters['max_salary']) |
                    Q(salary_min__lte=filters['max_salary'])
                )
            
            if filters.get('posted_days_ago'):
                cutoff_date = timezone.now() - timedelta(days=filters['posted_days_ago'])
                queryset = queryset.filter(posted_date__gte=cutoff_date)
            
            # Pagination
            page = filters.get('page', 1)
            page_size = filters.get('page_size', 20)
            start = (page - 1) * page_size
            end = start + page_size
            
            total_count = queryset.count()
            jobs = queryset.order_by('-quality_score', '-posted_date')[start:end]
            
            serializer = JobPostingSerializer(jobs, many=True)
            
            return Response({
                'jobs': serializer.data,
                'total': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size,
                'filters_applied': filters
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScrapeJobsView(APIView):
    """Initiate job scraping from external sources"""
    
    def post(self, request):
        serializer = ScrapeJobsSerializer(data=request.data)
        if serializer.is_valid():
            # Queue job scraping task
            task = scrape_jobs_from_sources.delay(
                sources=serializer.validated_data['sources'],
                search_terms=serializer.validated_data['search_terms'],
                location=serializer.validated_data.get('location'),
                limit_per_source=serializer.validated_data.get('limit_per_source', 50)
            )
            
            return Response({
                'message': 'Job scraping initiated',
                'task_id': task.id,
                'sources': serializer.validated_data['sources'],
                'search_terms': serializer.validated_data['search_terms']
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobRecommendationsView(APIView):
    """Get job recommendations for a user"""
    
    def get(self, request, user_id, job_id=None):
        try:
            user_profile = UserProfile.objects.get(id=user_id)
            
            if job_id:
                # Get recommendations for a specific job
                job = get_object_or_404(JobPosting, id=job_id)
                # Implementation for single job recommendations
                return Response({'message': 'Single job recommendations not implemented yet'})
            else:
                # Get general job recommendations for user
                matches = JobMatch.objects.filter(
                    user_profile=user_profile
                ).order_by('-overall_match_score')[:20]
                
                serializer = JobMatchSerializer(matches, many=True)
                return Response({
                    'recommendations': serializer.data,
                    'user_id': str(user_id),
                    'total_matches': matches.count()
                })
                
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class JobMatchView(APIView):
    """Get job match analysis for a user and specific job"""
    
    def get(self, request, user_id, job_id):
        try:
            user_profile = UserProfile.objects.get(id=user_id)
            processed_job = ProcessedJob.objects.get(original_job_id=job_id)
            
            try:
                job_match = JobMatch.objects.get(
                    user_profile=user_profile,
                    job=processed_job
                )
                
                # Mark as viewed
                if not job_match.viewed:
                    job_match.viewed = True
                    job_match.save()
                
                serializer = JobMatchSerializer(job_match)
                return Response(serializer.data)
                
            except JobMatch.DoesNotExist:
                return Response(
                    {'error': 'Job match not found. Job may not be processed yet.'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except (UserProfile.DoesNotExist, ProcessedJob.DoesNotExist):
            return Response(
                {'error': 'User or job not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class MarketAnalysisView(APIView):
    """Get market analysis and trends"""
    
    def post(self, request):
        # Extract parameters
        industry = request.data.get('industry')
        location = request.data.get('location')
        time_period = request.data.get('time_period', 30)  # days
        
        # Calculate market insights
        cutoff_date = timezone.now() - timedelta(days=time_period)
        
        base_query = JobPosting.objects.filter(
            is_active=True,
            is_processed=True,
            posted_date__gte=cutoff_date
        )
        
        if industry:
            base_query = base_query.filter(
                Q(company__industry__icontains=industry) |
                Q(processed_data__ai_industry_category__icontains=industry)
            )
        
        if location:
            base_query = base_query.filter(location__icontains=location)
        
        # Calculate statistics
        total_jobs = base_query.count()
        avg_salary = None
        
        # Get top companies
        top_companies = (
            base_query.values('company__name')
            .annotate(job_count=models.Count('id'))
            .order_by('-job_count')[:10]
        )
        
        # Get top skills (from processed jobs)
        # This would require aggregating skills from processed data
        
        return Response({
            'analysis_period': f'Last {time_period} days',
            'total_jobs': total_jobs,
            'industry': industry,
            'location': location,
            'top_companies': list(top_companies),
            'average_salary': avg_salary,
            'generated_at': timezone.now().isoformat()
        })