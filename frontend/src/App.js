import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentView, setCurrentView] = useState('home');
  const [userProfile, setUserProfile] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [jobDescription, setJobDescription] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [careerQuery, setCareerQuery] = useState('');
  const [careerAdvice, setCareerAdvice] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Anonymous search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState('general');
  const [searchResult, setSearchResult] = useState(null);
  const [popularTopics, setPopularTopics] = useState(null);

  // Profile form state
  const [profileForm, setProfileForm] = useState({
    name: '',
    education_level: '',
    field_of_study: '',
    skills: '',
    experience_years: 0,
    current_role: '',
    career_interests: ''
  });

  // Load profiles and popular topics on component mount
  useEffect(() => {
    loadProfiles();
    loadPopularTopics();
  }, []);

  const loadProfiles = async () => {
    try {
      const response = await axios.get(`${API}/profiles`);
      setProfiles(response.data);
      if (response.data.length > 0) {
        setUserProfile(response.data[0]); // Select first profile by default
      }
    } catch (error) {
      console.error('Error loading profiles:', error);
    }
  };

  const loadPopularTopics = async () => {
    try {
      const response = await axios.get(`${API}/popular-topics`);
      setPopularTopics(response.data);
    } catch (error) {
      console.error('Error loading popular topics:', error);
    }
  };

  const performAnonymousSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/search`, {
        query: searchQuery,
        search_type: searchType
      });
      setSearchResult(response.data);
      setCurrentView('search-result');
    } catch (error) {
      console.error('Error performing search:', error);
      alert('Error performing search. Please try again.');
    }
    setLoading(false);
  };

  const createProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const profileData = {
        ...profileForm,
        skills: profileForm.skills.split(',').map(s => s.trim()).filter(s => s),
        career_interests: profileForm.career_interests.split(',').map(s => s.trim()).filter(s => s)
      };
      
      const response = await axios.post(`${API}/profiles`, profileData);
      setUserProfile(response.data);
      setProfiles([...profiles, response.data]);
      setCurrentView('dashboard');
      setProfileForm({
        name: '',
        education_level: '',
        field_of_study: '',
        skills: '',
        experience_years: 0,
        current_role: '',
        career_interests: ''
      });
    } catch (error) {
      console.error('Error creating profile:', error);
      alert('Error creating profile. Please try again.');
    }
    setLoading(false);
  };

  const analyzeJob = async (e) => {
    e.preventDefault();
    if (!userProfile) {
      alert('Please create a profile first');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/analyze-job`, {
        user_id: userProfile.id,
        job_description: jobDescription
      });
      setAnalysisResult(response.data);
      setCurrentView('analysis-result');
    } catch (error) {
      console.error('Error analyzing job:', error);
      alert('Error analyzing job. Please try again.');
    }
    setLoading(false);
  };

  const getCareerAdvice = async (e) => {
    e.preventDefault();
    if (!userProfile) {
      alert('Please create a profile first');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/career-advice`, {
        user_id: userProfile.id,
        query: careerQuery
      });
      setCareerAdvice(response.data);
      setCurrentView('advice-result');
    } catch (error) {
      console.error('Error getting career advice:', error);
      alert('Error getting career advice. Please try again.');
    }
    setLoading(false);
  };

  const HomeView = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-800 mb-6">
            🎯 Career Navigator
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            Your AI-powered career advisor that analyzes job descriptions, provides personalized recommendations, and guides your professional journey.
          </p>
        </div>

        {/* Anonymous Search Section */}
        <div className="max-w-4xl mx-auto mb-16">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">
              🔍 Ask Any Career Question
            </h2>
            <p className="text-center text-gray-600 mb-6">
              Get instant AI-powered career guidance - no registration required!
            </p>
            
            <form onSubmit={performAnonymousSearch} className="space-y-4">
              <div className="flex gap-4 mb-4">
                <select
                  value={searchType}
                  onChange={(e) => setSearchType(e.target.value)}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="general">General Career Advice</option>
                  <option value="career_path">Career Paths</option>
                  <option value="skills">Skills Development</option>
                  <option value="industry">Industry Insights</option>
                  <option value="academic_pathways">Academic Pathways</option>
                </select>
              </div>
              
              <div className="relative">
                <textarea
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Ask anything about careers... e.g., 'How do I break into data science?' or 'What skills do I need for product management?'"
                  rows="3"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  required
                />
              </div>
              
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-3 rounded-lg font-semibold transition-all transform hover:scale-105 disabled:opacity-50 disabled:transform-none"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <div className="loading-spinner mr-2"></div>
                    Searching...
                  </span>
                ) : (
                  'Get Career Guidance 🚀'
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Popular Topics Section */}
        {popularTopics && (
          <div className="max-w-6xl mx-auto mb-16">
            <h3 className="text-2xl font-bold text-center mb-8 text-gray-800">
              🔥 Trending Career Topics
            </h3>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="bg-white p-6 rounded-xl shadow-lg">
                <h4 className="font-semibold text-lg mb-4 text-blue-600">Hot Careers</h4>
                <div className="space-y-2">
                  {popularTopics.trending_careers?.slice(0, 6).map((career, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        setSearchQuery(`Tell me about ${career} career path`);
                        setSearchType('career_path');
                      }}
                      className="block w-full text-left text-sm text-gray-700 hover:text-blue-600 hover:bg-blue-50 px-2 py-1 rounded transition-colors"
                    >
                      {career}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-xl shadow-lg">
                <h4 className="font-semibold text-lg mb-4 text-green-600">Popular Questions</h4>
                <div className="space-y-2">
                  {popularTopics.popular_questions?.slice(0, 6).map((question, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        setSearchQuery(question);
                        setSearchType('general');
                      }}
                      className="block w-full text-left text-sm text-gray-700 hover:text-green-600 hover:bg-green-50 px-2 py-1 rounded transition-colors"
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className="bg-white p-6 rounded-xl shadow-lg">
                <h4 className="font-semibold text-lg mb-4 text-purple-600">Industry Insights</h4>
                <div className="space-y-2">
                  {popularTopics.industry_insights?.slice(0, 6).map((industry, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        setSearchQuery(`What are the career opportunities in ${industry}?`);
                        setSearchType('industry');
                      }}
                      className="block w-full text-left text-sm text-gray-700 hover:text-purple-600 hover:bg-purple-50 px-2 py-1 rounded transition-colors"
                    >
                      {industry}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="text-center mb-16">
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => setCurrentView('create-profile')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
            >
              Create Profile for Personalized Advice
            </button>
            {userProfile && (
              <button
                onClick={() => setCurrentView('dashboard')}
                className="bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors"
              >
                Go to Dashboard
              </button>
            )}
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <div className="bg-white p-6 rounded-xl shadow-lg card-hover">
            <div className="text-4xl mb-4">🎓</div>
            <h3 className="text-xl font-semibold mb-3">For Students</h3>
            <p className="text-gray-600">
              Discover career paths, understand job requirements, and plan your educational journey.
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-lg card-hover">
            <div className="text-4xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold mb-3">For Graduates</h3>
            <p className="text-gray-600">
              Find job opportunities that match your qualifications and get insights on companies in your field.
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-lg card-hover">
            <div className="text-4xl mb-4">📈</div>
            <h3 className="text-xl font-semibold mb-3">For Professionals</h3>
            <p className="text-gray-600">
              Stay updated with job market trends and advance your career with strategic insights.
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  const CreateProfileView = () => (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-4">
        <div className="max-w-2xl mx-auto bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-3xl font-bold text-center mb-8">Create Your Profile</h2>
          
          <form onSubmit={createProfile} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
              <input
                type="text"
                required
                value={profileForm.name}
                onChange={(e) => setProfileForm({...profileForm, name: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Education Level</label>
              <select
                required
                value={profileForm.education_level}
                onChange={(e) => setProfileForm({...profileForm, education_level: e.target.value})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Select Education Level</option>
                <option value="High School">High School</option>
                <option value="Associate Degree">Associate Degree</option>
                <option value="Bachelor's Degree">Bachelor's Degree</option>
                <option value="Master's Degree">Master's Degree</option>
                <option value="PhD">PhD</option>
                <option value="Professional Certification">Professional Certification</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Field of Study</label>
              <input
                type="text"
                value={profileForm.field_of_study}
                onChange={(e) => setProfileForm({...profileForm, field_of_study: e.target.value})}
                placeholder="e.g., Computer Science, Business, Engineering"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Skills (comma-separated)</label>
              <input
                type="text"
                value={profileForm.skills}
                onChange={(e) => setProfileForm({...profileForm, skills: e.target.value})}
                placeholder="e.g., Python, Project Management, Data Analysis"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Years of Experience</label>
              <input
                type="number"
                min="0"
                value={profileForm.experience_years}
                onChange={(e) => setProfileForm({...profileForm, experience_years: parseInt(e.target.value) || 0})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Current Role (optional)</label>
              <input
                type="text"
                value={profileForm.current_role}
                onChange={(e) => setProfileForm({...profileForm, current_role: e.target.value})}
                placeholder="e.g., Software Developer, Student, Marketing Manager"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Career Interests (comma-separated)</label>
              <input
                type="text"
                value={profileForm.career_interests}
                onChange={(e) => setProfileForm({...profileForm, career_interests: e.target.value})}
                placeholder="e.g., Technology, Healthcare, Finance, Education"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="flex space-x-4">
              <button
                type="button"
                onClick={() => setCurrentView('home')}
                className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Profile'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );

  const DashboardView = () => (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-800">Career Dashboard</h1>
            <div className="flex space-x-4">
              <button
                onClick={() => setCurrentView('home')}
                className="text-gray-600 hover:text-gray-800"
              >
                Home
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {userProfile && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">Welcome back, {userProfile.name}!</h2>
            <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-600">
              <div>
                <strong>Education:</strong> {userProfile.education_level}
                {userProfile.field_of_study && ` in ${userProfile.field_of_study}`}
              </div>
              <div>
                <strong>Experience:</strong> {userProfile.experience_years} years
              </div>
              <div>
                <strong>Skills:</strong> {userProfile.skills?.join(', ') || 'None specified'}
              </div>
              <div>
                <strong>Interests:</strong> {userProfile.career_interests?.join(', ') || 'None specified'}
              </div>
            </div>
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-8">
          {/* Job Analysis Section */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-semibold mb-4">📋 Analyze Job Description</h3>
            <p className="text-gray-600 mb-4">
              Paste a job description to get detailed analysis and personalized recommendations.
            </p>
            
            <form onSubmit={analyzeJob}>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the job description here..."
                rows="6"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-4"
                required
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors disabled:opacity-50"
              >
                {loading ? 'Analyzing...' : 'Analyze Job'}
              </button>
            </form>
          </div>

          {/* Career Advice Section */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-xl font-semibold mb-4">💡 Get Career Advice</h3>
            <p className="text-gray-600 mb-4">
              Ask any career-related question and get personalized AI-powered advice.
            </p>
            
            <form onSubmit={getCareerAdvice}>
              <textarea
                value={careerQuery}
                onChange={(e) => setCareerQuery(e.target.value)}
                placeholder="What career advice do you need? e.g., 'How can I transition into data science?' or 'What skills should I develop for product management?'"
                rows="4"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent mb-4"
                required
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors disabled:opacity-50"
              >
                {loading ? 'Getting Advice...' : 'Get Advice'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );

  const AnalysisResultView = () => (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800">Job Analysis Results</h2>
              <button
                onClick={() => setCurrentView('dashboard')}
                className="text-blue-600 hover:text-blue-800"
              >
                ← Back to Dashboard
              </button>
            </div>

            {analysisResult && (
              <div className="space-y-6">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-blue-800 mb-2">Match Score</h3>
                  <div className="flex items-center">
                    <div className="w-full bg-blue-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{width: `${analysisResult.match_score * 100}%`}}
                      ></div>
                    </div>
                    <span className="ml-3 text-blue-800 font-semibold">
                      {Math.round(analysisResult.match_score * 100)}%
                    </span>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-800 mb-3">📊 Job Analysis</h3>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700">
                      {typeof analysisResult.analysis === 'object' 
                        ? JSON.stringify(analysisResult.analysis, null, 2)
                        : analysisResult.analysis
                      }
                    </pre>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-800 mb-3">💡 Recommendations</h3>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-sm text-gray-700 whitespace-pre-wrap">
                      {Array.isArray(analysisResult.recommendations) 
                        ? analysisResult.recommendations.join('\n\n')
                        : analysisResult.recommendations
                      }
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-800 mb-3">📝 Original Job Description</h3>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-sm text-gray-700 whitespace-pre-wrap">
                      {analysisResult.job_description}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const AdviceResultView = () => (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800">Career Advice</h2>
              <button
                onClick={() => setCurrentView('dashboard')}
                className="text-blue-600 hover:text-blue-800"
              >
                ← Back to Dashboard
              </button>
            </div>

            {careerAdvice && (
              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold text-gray-800 mb-3">❓ Your Question</h3>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-gray-700">{careerAdvice.query}</p>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-800 mb-3">💡 AI Career Advice</h3>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-gray-700 whitespace-pre-wrap">
                      {careerAdvice.advice}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const SearchResultView = () => (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-gray-800">Career Search Results</h2>
              <button
                onClick={() => setCurrentView('home')}
                className="text-blue-600 hover:text-blue-800"
              >
                ← Back to Home
              </button>
            </div>

            {searchResult && (
              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold text-gray-800 mb-3">🔍 Your Search</h3>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-gray-700 font-medium">{searchResult.query}</p>
                    <p className="text-sm text-blue-600 mt-1">
                      Search Type: {searchResult.search_type.replace('_', ' ').toUpperCase()}
                    </p>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-800 mb-3">💡 AI Career Guidance</h3>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-gray-700 whitespace-pre-wrap">
                      {searchResult.response}
                    </div>
                  </div>
                </div>

                {searchResult.suggestions && searchResult.suggestions.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-800 mb-3">🎯 Related Topics</h3>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 mb-3">You might also be interested in:</p>
                      <div className="space-y-2">
                        {searchResult.suggestions.map((suggestion, index) => (
                          <button
                            key={index}
                            onClick={() => {
                              setSearchQuery(suggestion);
                              setCurrentView('home');
                              // Auto-scroll to search form
                              setTimeout(() => {
                                document.querySelector('textarea')?.focus();
                              }, 100);
                            }}
                            className="block w-full text-left text-sm text-purple-700 hover:text-purple-900 hover:bg-purple-100 px-3 py-2 rounded transition-colors"
                          >
                            📌 {suggestion}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                <div className="text-center pt-6 border-t border-gray-200">
                  <p className="text-gray-600 mb-4">Want more personalized advice?</p>
                  <button
                    onClick={() => setCurrentView('create-profile')}
                    className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-lg font-semibold transition-all"
                  >
                    Create Profile for Personalized Guidance
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  // Render based on current view
  const renderView = () => {
    switch(currentView) {
      case 'create-profile':
        return <CreateProfileView />;
      case 'dashboard':
        return <DashboardView />;
      case 'analysis-result':
        return <AnalysisResultView />;
      case 'advice-result':
        return <AdviceResultView />;
      case 'search-result':
        return <SearchResultView />;
      default:
        return <HomeView />;
    }
  };

  return (
    <div className="App">
      {renderView()}
    </div>
  );
}

export default App;