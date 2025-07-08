#!/usr/bin/env python3
import requests
import json
import uuid
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://5b3a5c9a-6404-4135-8757-1eb6a9993556.preview.emergentagent.com/api"
TEST_RESULTS = {}

# Test data
SAMPLE_PROFILE = {
    "name": "Alex Johnson",
    "education_level": "Master's",
    "field_of_study": "Computer Science",
    "skills": ["Python", "Machine Learning", "Data Analysis", "Cloud Computing", "SQL"],
    "experience_years": 3,
    "current_role": "Data Scientist",
    "career_interests": ["AI Research", "Machine Learning Engineering", "Data Engineering"]
}

SAMPLE_JOB_DESCRIPTION = """
Senior Machine Learning Engineer

Company: TechInnovate AI
Location: Remote (US-based)

Job Description:
We are seeking an experienced Machine Learning Engineer to join our growing AI team. The ideal candidate will have a strong background in developing and deploying machine learning models at scale.

Requirements:
- Master's or PhD in Computer Science, Machine Learning, or related field
- 5+ years of experience in machine learning engineering
- Proficiency in Python and ML frameworks (TensorFlow, PyTorch)
- Experience with cloud platforms (AWS, GCP, or Azure)
- Strong understanding of data structures, algorithms, and software design
- Experience with large language models and generative AI is a plus

Responsibilities:
- Design, develop, and deploy machine learning models
- Collaborate with data scientists and product teams
- Optimize model performance and scalability
- Implement MLOps best practices
- Stay current with the latest ML research and technologies

Salary Range: $140,000 - $180,000 depending on experience
"""

SAMPLE_CAREER_QUESTION = "Given my background in data science with 3 years of experience, what skills should I focus on developing to transition into a more senior machine learning engineering role in the next 2 years?"

# Anonymous search test data
ANONYMOUS_SEARCH_QUERIES = {
    "general": "What are the best career paths for someone with a background in psychology?",
    "career_path": "How can I progress from a junior software developer to a senior role?",
    "skills": "What skills are most in-demand for data scientists in 2025?",
    "industry": "What is the job market outlook for renewable energy sector in the next 5 years?"
}

# Helper functions
def print_header(title):
    """Print a formatted header for test sections"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80 + "\n")

def make_request(method, endpoint, data=None, params=None) -> Dict[str, Any]:
    """Make an HTTP request to the API and return the response"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.lower() == "get":
            response = requests.get(url, params=params)
        elif method.lower() == "post":
            response = requests.post(url, json=data)
        elif method.lower() == "put":
            response = requests.put(url, json=data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Try to parse JSON response
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = {"text": response.text}
        
        return {
            "status_code": response.status_code,
            "success": 200 <= response.status_code < 300,
            "data": result
        }
    except requests.RequestException as e:
        return {
            "status_code": 0,
            "success": False,
            "error": str(e),
            "data": None
        }

def run_test(test_name, method, endpoint, data=None, params=None, expected_status=200) -> bool:
    """Run a test and record the result"""
    print(f"Testing: {test_name}...")
    
    result = make_request(method, endpoint, data, params)
    success = result["success"] and result["status_code"] == expected_status
    
    if success:
        print(f"✅ PASSED: {test_name}")
    else:
        print(f"❌ FAILED: {test_name}")
        print(f"  Status Code: {result['status_code']} (Expected: {expected_status})")
        if "error" in result:
            print(f"  Error: {result['error']}")
    
    # Store detailed result for summary
    TEST_RESULTS[test_name] = {
        "success": success,
        "status_code": result["status_code"],
        "expected_status": expected_status,
        "data": result["data"]
    }
    
    return result

def print_summary():
    """Print a summary of all test results"""
    print_header("TEST SUMMARY")
    
    passed = sum(1 for result in TEST_RESULTS.values() if result["success"])
    total = len(TEST_RESULTS)
    
    print(f"PASSED: {passed}/{total} ({passed/total*100:.1f}%)")
    print("\nDetails:")
    
    for test_name, result in TEST_RESULTS.items():
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print("\n")

# Main test functions
def test_health_check():
    """Test the basic health check endpoint"""
    print_header("TESTING HEALTH CHECK")
    return run_test("API Health Check", "get", "/")

def test_profile_creation():
    """Test creating a user profile"""
    print_header("TESTING PROFILE CREATION")
    return run_test("Create User Profile", "post", "/profiles", SAMPLE_PROFILE)

def test_get_profiles():
    """Test retrieving all profiles"""
    print_header("TESTING GET ALL PROFILES")
    return run_test("Get All Profiles", "get", "/profiles")

def test_get_profile_by_id(profile_id):
    """Test retrieving a specific profile by ID"""
    print_header("TESTING GET PROFILE BY ID")
    return run_test(f"Get Profile by ID: {profile_id}", "get", f"/profiles/{profile_id}")

def test_update_profile(profile_id):
    """Test updating a user profile"""
    print_header("TESTING PROFILE UPDATE")
    updated_profile = SAMPLE_PROFILE.copy()
    updated_profile["skills"] = SAMPLE_PROFILE["skills"] + ["Deep Learning", "NLP"]
    updated_profile["experience_years"] = 4
    
    return run_test(f"Update Profile: {profile_id}", "put", f"/profiles/{profile_id}", updated_profile)

def test_job_analysis(profile_id):
    """Test job description analysis"""
    print_header("TESTING JOB ANALYSIS")
    job_request = {
        "user_id": profile_id,
        "job_description": SAMPLE_JOB_DESCRIPTION
    }
    
    return run_test("Analyze Job Description", "post", "/analyze-job", job_request)

def test_career_advice(profile_id):
    """Test career advice endpoint"""
    print_header("TESTING CAREER ADVICE")
    advice_request = {
        "user_id": profile_id,
        "query": SAMPLE_CAREER_QUESTION
    }
    
    return run_test("Get Career Advice", "post", "/career-advice", advice_request)

def test_market_insights():
    """Test market insights endpoint"""
    print_header("TESTING MARKET INSIGHTS")
    field = "machine learning"
    
    return run_test(f"Get Market Insights for {field}", "get", f"/market-insights/{field}")

def test_error_handling():
    """Test error handling for non-existent profile"""
    print_header("TESTING ERROR HANDLING")
    fake_id = str(uuid.uuid4())
    
    return run_test("Error Handling - Profile Not Found", "get", f"/profiles/{fake_id}", expected_status=404)

def test_anonymous_search():
    """Test anonymous search API with different search types"""
    print_header("TESTING ANONYMOUS SEARCH API")
    
    results = {}
    
    # Test each search type
    for search_type, query in ANONYMOUS_SEARCH_QUERIES.items():
        search_request = {
            "query": query,
            "search_type": search_type
        }
        
        result = run_test(f"Anonymous Search - {search_type}", "post", "/search", search_request)
        results[search_type] = result
        
        # Verify response structure if successful
        if result["success"]:
            data = result["data"]
            if "response" in data and "suggestions" in data:
                print(f"  ✓ Response contains expected fields")
                print(f"  ✓ Got {len(data['suggestions'])} suggestions")
            else:
                print(f"  ⚠ Response missing expected fields")
        
        # Add a small delay between requests to avoid rate limiting
        time.sleep(1)
    
    return results

def test_popular_topics():
    """Test popular topics endpoint"""
    print_header("TESTING POPULAR TOPICS")
    
    result = run_test("Get Popular Topics", "get", "/popular-topics")
    
    # Verify response structure if successful
    if result["success"]:
        data = result["data"]
        expected_keys = ["trending_careers", "popular_questions", "industry_insights"]
        
        all_keys_present = all(key in data for key in expected_keys)
        if all_keys_present:
            print(f"  ✓ Response contains all expected categories")
            for key in expected_keys:
                print(f"  ✓ {key}: {len(data[key])} items")
        else:
            print(f"  ⚠ Response missing some expected categories")
    
    return result

def test_openai_integration():
    """Test OpenAI integration with the new API key"""
    print_header("TESTING OPENAI INTEGRATION")
    
    # We'll use the anonymous search endpoint to test OpenAI integration
    # since it directly uses the OpenAI API without requiring a user profile
    search_request = {
        "query": "What are the most important skills for a data scientist in 2025?",
        "search_type": "general"
    }
    
    result = run_test("OpenAI Integration via Anonymous Search", "post", "/search", search_request)
    
    # Check if we got a meaningful response that indicates OpenAI is working
    if result["success"]:
        data = result["data"]
        if "response" in data and len(data["response"]) > 100:
            print(f"  ✓ Received substantial AI-generated response ({len(data['response'])} chars)")
            print(f"  ✓ OpenAI integration appears to be working correctly")
        else:
            print(f"  ⚠ Response seems too short or empty, OpenAI may not be working properly")
    
    return result

def main():
    """Run all tests in sequence"""
    print_header("CAREER ADVISOR API TESTING")
    print(f"Testing API at: {BASE_URL}")
    
    # Test basic health check
    health_result = test_health_check()
    
    if not health_result["success"]:
        print("❌ API health check failed. Aborting remaining tests.")
        return
    
    # Test anonymous search API (primary focus)
    anonymous_search_results = test_anonymous_search()
    
    # Test popular topics endpoint
    popular_topics_result = test_popular_topics()
    
    # Test OpenAI integration with the new API key
    openai_integration_result = test_openai_integration()
    
    # Test profile creation and get the profile ID
    profile_result = test_profile_creation()
    
    if profile_result["success"] and "data" in profile_result and "id" in profile_result["data"]:
        profile_id = profile_result["data"]["id"]
        print(f"Created test profile with ID: {profile_id}")
        
        # Run tests that depend on having a profile
        test_get_profiles()
        test_get_profile_by_id(profile_id)
        test_update_profile(profile_id)
        
        # Test AI-powered endpoints
        job_result = test_job_analysis(profile_id)
        advice_result = test_career_advice(profile_id)
        
        # These tests don't depend on the profile
        test_market_insights()
        test_error_handling()
    else:
        print("❌ Profile creation failed. Skipping profile-dependent tests.")
    
    # Print summary of all tests
    print_summary()

if __name__ == "__main__":
    main()