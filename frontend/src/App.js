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

  const HeaderNav = () => (
    <nav className="bg-white shadow-lg border-b-4 border-gradient-to-r from-purple-500 to-pink-500">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center space-x-3">
            <img 
              src="https://github.com/Simonwafula/Nextstepjobs/blob/main/Nextstep%20logo.jpeg?raw=true" 
              alt="NextStep Logo" 
              className="h-12 w-auto"
            />
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                NextStep
              </h1>
              <p className="text-xs text-gray-500 font-medium">Your Career Evolution Partner</p>
            </div>
          </div>
          
          <div className="flex space-x-4">
            <button
              onClick={() => setCurrentView('home')}
              className={`px-4 py-2 rounded-full font-medium transition-all ${
                currentView === 'home' 
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg' 
                  : 'text-gray-600 hover:text-purple-600 hover:bg-purple-50'
              }`}
            >
              Home
            </button>
            {userProfile && (
              <button
                onClick={() => setCurrentView('dashboard')}
                className={`px-4 py-2 rounded-full font-medium transition-all ${
                  currentView === 'dashboard' 
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg' 
                    : 'text-gray-600 hover:text-purple-600 hover:bg-purple-50'
                }`}
              >
                Dashboard
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );

  const HomeView = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50">
      <HeaderNav />
      
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16 relative">
          <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-pink-400 opacity-10 rounded-3xl"></div>
          <div className="relative z-10 p-8">
            <h1 className="text-6xl font-bold mb-6 animate-pulse">
              <span className="bg-gradient-to-r from-purple-600 via-pink-600 to-indigo-600 bg-clip-text text-transparent">
                Your Next Step
              </span>
              <br />
              <span className="text-gray-800">Starts Here! 🚀</span>
            </h1>
            <p className="text-xl text-gray-700 max-w-4xl mx-auto mb-8 leading-relaxed">
              Unlock your career potential with AI-powered insights, personalized job analysis, and strategic career guidance. 
              Transform your professional journey with NextStep - where ambition meets opportunity! ✨
            </p>
            <div className="flex justify-center space-x-4">
              <div className="flex items-center space-x-2 bg-white/80 backdrop-blur-sm rounded-full px-6 py-3 shadow-lg">
                <span className="text-2xl">🎯</span>
                <span className="font-semibold text-gray-800">Smart Job Matching</span>
              </div>
              <div className="flex items-center space-x-2 bg-white/80 backdrop-blur-sm rounded-full px-6 py-3 shadow-lg">
                <span className="text-2xl">🧠</span>
                <span className="font-semibold text-gray-800">AI Career Insights</span>
              </div>
              <div className="flex items-center space-x-2 bg-white/80 backdrop-blur-sm rounded-full px-6 py-3 shadow-lg">
                <span className="text-2xl">📈</span>
                <span className="font-semibold text-gray-800">Growth Tracking</span>
              </div>
            </div>
          </div>
        </div>

        {/* Anonymous Search Section */}
        <div className="max-w-4xl mx-auto mb-16">
          <div className="bg-white/90 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-purple-100">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-4">
                <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  Ask NextStep Anything! 🔮
                </span>
              </h2>
              <p className="text-gray-600 text-lg">
                Get instant AI-powered career guidance - no strings attached, no sign-up required!
              </p>
            </div>
            
            <form onSubmit={performAnonymousSearch} className="space-y-6">
              <div className="flex gap-4 mb-6">
                <select
                  value={searchType}
                  onChange={(e) => setSearchType(e.target.value)}
                  className="px-6 py-3 border-2 border-purple-200 rounded-2xl focus:ring-4 focus:ring-purple-200 focus:border-purple-500 transition-all bg-white/80 backdrop-blur-sm font-medium"
                >
                  <option value="general">💬 General Career Advice</option>
                  <option value="career_path">🛤️ Career Paths</option>
                  <option value="skills">🎯 Skills Development</option>
                  <option value="industry">🏢 Industry Insights</option>
                </select>
              </div>
              
              <div className="relative">
                <textarea
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="🌟 Ask anything about your career journey... 'How do I break into AI?' or 'What's the future of remote work?' or 'Best skills for 2025?'"
                  rows="4"
                  className="w-full px-6 py-4 border-2 border-purple-200 rounded-2xl focus:ring-4 focus:ring-purple-200 focus:border-purple-500 transition-all resize-none bg-white/80 backdrop-blur-sm text-gray-800 placeholder-gray-500"
                  required
                />
                <div className="absolute bottom-3 right-3 text-purple-400">
                  <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"></path>
                    <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"></path>
                  </svg>
                </div>
              </div>
              
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-purple-600 via-pink-600 to-indigo-600 hover:from-purple-700 hover:via-pink-700 hover:to-indigo-700 text-white px-8 py-4 rounded-2xl font-bold text-lg transition-all transform hover:scale-105 hover:shadow-2xl disabled:opacity-50 disabled:transform-none"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <div className="nextstep-spinner mr-3"></div>
                    Analyzing Your Future...
                  </span>
                ) : (
                  <>
                    <span className="mr-2">🚀</span>
                    Discover Your Next Step
                    <span className="ml-2">✨</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Popular Topics Section */}
        {popularTopics && (
          <div className="max-w-7xl mx-auto mb-16">
            <h3 className="text-4xl font-bold text-center mb-12">
              <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                🔥 What's Trending in Careers
              </span>
            </h3>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-8 rounded-3xl shadow-2xl text-white transform hover:scale-105 transition-all">
                <h4 className="font-bold text-2xl mb-6 flex items-center">
                  <span className="mr-3">🚀</span>
                  Hot Careers
                </h4>
                <div className="space-y-3">
                  {popularTopics.trending_careers?.slice(0, 6).map((career, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        setSearchQuery(`Tell me about ${career} career path and opportunities`);
                        setSearchType('career_path');
                      }}
                      className="block w-full text-left text-sm text-purple-100 hover:text-white hover:bg-purple-400/50 px-4 py-3 rounded-xl transition-all backdrop-blur-sm"
                    >
                      ✨ {career}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className="bg-gradient-to-br from-pink-500 to-pink-600 p-8 rounded-3xl shadow-2xl text-white transform hover:scale-105 transition-all">
                <h4 className="font-bold text-2xl mb-6 flex items-center">
                  <span className="mr-3">💡</span>
                  Popular Questions
                </h4>
                <div className="space-y-3">
                  {popularTopics.popular_questions?.slice(0, 6).map((question, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        setSearchQuery(question);
                        setSearchType('general');
                      }}
                      className="block w-full text-left text-sm text-pink-100 hover:text-white hover:bg-pink-400/50 px-4 py-3 rounded-xl transition-all backdrop-blur-sm"
                    >
                      🤔 {question}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 p-8 rounded-3xl shadow-2xl text-white transform hover:scale-105 transition-all">
                <h4 className="font-bold text-2xl mb-6 flex items-center">
                  <span className="mr-3">🏢</span>
                  Industry Insights
                </h4>
                <div className="space-y-3">
                  {popularTopics.industry_insights?.slice(0, 6).map((industry, index) => (
                    <button
                      key={index}
                      onClick={() => {
                        setSearchQuery(`What are the latest trends and opportunities in ${industry}?`);
                        setSearchType('industry');
                      }}
                      className="block w-full text-left text-sm text-indigo-100 hover:text-white hover:bg-indigo-400/50 px-4 py-3 rounded-xl transition-all backdrop-blur-sm"
                    >
                      🌟 {industry}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="text-center mb-16">
          <div className="flex justify-center space-x-6">
            <button
              onClick={() => setCurrentView('create-profile')}
              className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white px-8 py-4 rounded-2xl font-bold text-lg transition-all transform hover:scale-105 shadow-2xl"
            >
              <span className="mr-2">👤</span>
              Create Profile for Personalized Magic
            </button>
            {userProfile && (
              <button
                onClick={() => setCurrentView('dashboard')}
                className="bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700 text-white px-8 py-4 rounded-2xl font-bold text-lg transition-all transform hover:scale-105 shadow-2xl"
              >
                <span className="mr-2">📊</span>
                Go to Dashboard
              </button>
            )}
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 max-w-7xl mx-auto">
          <div className="bg-gradient-to-br from-purple-100 to-pink-100 p-8 rounded-3xl shadow-xl transform hover:scale-105 transition-all border-2 border-purple-200">
            <div className="text-6xl mb-6 text-center">🎓</div>
            <h3 className="text-2xl font-bold mb-4 text-center bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              For Students
            </h3>
            <p className="text-gray-700 text-center leading-relaxed">
              Discover your perfect career path, understand industry requirements, and plan your educational journey with AI-powered insights.
            </p>
          </div>
          
          <div className="bg-gradient-to-br from-pink-100 to-indigo-100 p-8 rounded-3xl shadow-xl transform hover:scale-105 transition-all border-2 border-pink-200">
            <div className="text-6xl mb-6 text-center">🎯</div>
            <h3 className="text-2xl font-bold mb-4 text-center bg-gradient-to-r from-pink-600 to-indigo-600 bg-clip-text text-transparent">
              For Graduates
            </h3>
            <p className="text-gray-700 text-center leading-relaxed">
              Find job opportunities that match your qualifications, get company insights, and launch your career with confidence.
            </p>
          </div>
          
          <div className="bg-gradient-to-br from-indigo-100 to-purple-100 p-8 rounded-3xl shadow-xl transform hover:scale-105 transition-all border-2 border-indigo-200">
            <div className="text-6xl mb-6 text-center">📈</div>
            <h3 className="text-2xl font-bold mb-4 text-center bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              For Professionals
            </h3>
            <p className="text-gray-700 text-center leading-relaxed">
              Stay ahead with market trends, advance your career strategically, and discover new opportunities in your field.
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  const CreateProfileView = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50">
      <HeaderNav />
      
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-2xl mx-auto bg-white/90 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-purple-100">
          <div className="text-center mb-8">
            <h2 className="text-4xl font-bold mb-4">
              <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                Create Your NextStep Profile
              </span>
            </h2>
            <p className="text-gray-600">Let's personalize your career journey! ✨</p>
          </div>
          
          <form onSubmit={createProfile} className="space-y-6">
            <div>
              <label className="block text-sm font-bold text-gray-700 mb-3">✨ Full Name</label>
              <input
                type="text"
                required
                value={profileForm.name}
                onChange={(e) => setProfileForm({...profileForm, name: e.target.value})}
                className="w-full px-6 py-4 border-2 border-purple-200 rounded-2xl focus:ring-4 focus:ring-purple-200 focus:border-purple-500 transition-all bg-white/80 backdrop-blur-sm"
                placeholder="Your amazing name"
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-3">🎓 Education Level</label>
              <select
                required
                value={profileForm.education_level}
                onChange={(e) => setProfileForm({...profileForm, education_level: e.target.value})}
                className="w-full px-6 py-4 border-2 border-purple-200 rounded-2xl focus:ring-4 focus:ring-purple-200 focus:border-purple-500 transition-all bg-white/80 backdrop-blur-sm"
              >
                <option value="">Select Your Education Level</option>
                <option value="High School">High School</option>
                <option value="Associate Degree">Associate Degree</option>
                <option value="Bachelor's Degree">Bachelor's Degree</option>
                <option value="Master's Degree">Master's Degree</option>
                <option value="PhD">PhD</option>
                <option value="Professional Certification">Professional Certification</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-3">📚 Field of Study</label>
              <input
                type="text"
                value={profileForm.field_of_study}
                onChange={(e) => setProfileForm({...profileForm, field_of_study: e.target.value})}
                placeholder="e.g., Computer Science, Business, Engineering, Psychology"
                className="w-full px-6 py-4 border-2 border-purple-200 rounded-2xl focus:ring-4 focus:ring-purple-200 focus:border-purple-500 transition-all bg-white/80 backdrop-blur-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-3">🎯 Skills (comma-separated)</label>
              <input
                type="text"
                value={profileForm.skills}
                onChange={(e) => setProfileForm({...profileForm, skills: e.target.value})}
                placeholder="e.g., Python, Project Management, Data Analysis, Leadership"
                className="w-full px-6 py-4 border-2 border-purple-200 rounded-2xl focus:ring-4 focus:ring-purple-200 focus:border-purple-500 transition-all bg-white/80 backdrop-blur-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-3">⏰ Years of Experience</label>
              <input
                type="number"
                min="0"
                value={profileForm.experience_years}
                onChange={(e) => setProfileForm({...profileForm, experience_years: parseInt(e.target.value) || 0})}
                className="w-full px-6 py-4 border-2 border-purple-200 rounded-2xl focus:ring-4 focus:ring-purple-200 focus:border-purple-500 transition-all bg-white/80 backdrop-blur-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-3">💼 Current Role (optional)</label>
              <input
                type="text"
                value={profileForm.current_role}
                onChange={(e) => setProfileForm({...profileForm, current_role: e.target.value})}
                placeholder="e.g., Software Developer, Student, Marketing Manager"
                className="w-full px-6 py-4 border-2 border-purple-200 rounded-2xl focus:ring-4 focus:ring-purple-200 focus:border-purple-500 transition-all bg-white/80 backdrop-blur-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-bold text-gray-700 mb-3">💫 Career Interests (comma-separated)</label>
              <input
                type="text"
                value={profileForm.career_interests}
                onChange={(e) => setProfileForm({...profileForm, career_interests: e.target.value})}
                placeholder="e.g., Technology, Healthcare, Finance, Education, AI"
                className="w-full px-6 py-4 border-2 border-purple-200 rounded-2xl focus:ring-4 focus:ring-purple-200 focus:border-purple-500 transition-all bg-white/80 backdrop-blur-sm"
              />
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="button"
                onClick={() => setCurrentView('home')}
                className="flex-1 px-6 py-4 border-2 border-gray-300 text-gray-700 rounded-2xl hover:bg-gray-50 transition-all font-medium"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-6 py-4 rounded-2xl font-bold transition-all disabled:opacity-50 transform hover:scale-105"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <div className="nextstep-spinner mr-2"></div>
                    Creating Magic...
                  </span>
                ) : (
                  <>
                    <span className="mr-2">🚀</span>
                    Create My Profile
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );

  const DashboardView = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50">
      <HeaderNav />
      
      <div className="container mx-auto px-4 py-8">
        {userProfile && (
          <div className="bg-gradient-to-r from-purple-500 to-pink-500 rounded-3xl shadow-2xl p-8 mb-8 text-white">
            <h2 className="text-3xl font-bold mb-6 flex items-center">
              <span className="mr-3">👋</span>
              Welcome back, {userProfile.name}!
            </h2>
            <div className="grid md:grid-cols-2 gap-6 text-sm">
              <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-4">
                <strong className="flex items-center mb-2">
                  <span className="mr-2">🎓</span>
                  Education:
                </strong>
                <span>{userProfile.education_level}</span>
                {userProfile.field_of_study && <span> in {userProfile.field_of_study}</span>}
              </div>
              <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-4">
                <strong className="flex items-center mb-2">
                  <span className="mr-2">⏰</span>
                  Experience:
                </strong>
                <span>{userProfile.experience_years} years</span>
              </div>
              <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-4">
                <strong className="flex items-center mb-2">
                  <span className="mr-2">🎯</span>
                  Skills:
                </strong>
                <span>{userProfile.skills?.join(', ') || 'None specified'}</span>
              </div>
              <div className="bg-white/20 backdrop-blur-sm rounded-2xl p-4">
                <strong className="flex items-center mb-2">
                  <span className="mr-2">💫</span>
                  Interests:
                </strong>
                <span>{userProfile.career_interests?.join(', ') || 'None specified'}</span>
              </div>
            </div>
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-8">
          {/* Job Analysis Section */}
          <div className="bg-white/90 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-purple-100">
            <h3 className="text-2xl font-bold mb-6 flex items-center">
              <span className="mr-3">📋</span>
              <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                Analyze Job Description
              </span>
            </h3>
            <p className="text-gray-600 mb-6">
              Paste any job description and get AI-powered insights tailored to your profile! 🚀
            </p>
            
            <form onSubmit={analyzeJob}>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="✨ Paste the job description here and watch the magic happen..."
                rows="6"
                className="w-full px-6 py-4 border-2 border-purple-200 rounded-2xl focus:ring-4 focus:ring-purple-200 focus:border-purple-500 transition-all mb-4 bg-white/80 backdrop-blur-sm"
                required
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white px-6 py-4 rounded-2xl font-bold transition-all disabled:opacity-50 transform hover:scale-105"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <div className="nextstep-spinner mr-2"></div>
                    Analyzing...
                  </span>
                ) : (
                  <>
                    <span className="mr-2">🔍</span>
                    Analyze Job
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Career Advice Section */}
          <div className="bg-white/90 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-pink-100">
            <h3 className="text-2xl font-bold mb-6 flex items-center">
              <span className="mr-3">💡</span>
              <span className="bg-gradient-to-r from-pink-600 to-purple-600 bg-clip-text text-transparent">
                Get Career Advice
              </span>
            </h3>
            <p className="text-gray-600 mb-6">
              Ask anything about your career journey and get personalized AI guidance! 🌟
            </p>
            
            <form onSubmit={getCareerAdvice}>
              <textarea
                value={careerQuery}
                onChange={(e) => setCareerQuery(e.target.value)}
                placeholder="🤔 What's on your mind? Ask about career transitions, skill development, industry trends, or anything else!"
                rows="4"
                className="w-full px-6 py-4 border-2 border-pink-200 rounded-2xl focus:ring-4 focus:ring-pink-200 focus:border-pink-500 transition-all mb-4 bg-white/80 backdrop-blur-sm"
                required
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-700 hover:to-purple-700 text-white px-6 py-4 rounded-2xl font-bold transition-all disabled:opacity-50 transform hover:scale-105"
              >
                {loading ? (
                  <span className="flex items-center justify-center">
                    <div className="nextstep-spinner mr-2"></div>
                    Getting Advice...
                  </span>
                ) : (
                  <>
                    <span className="mr-2">💭</span>
                    Get Advice
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );

  const AnalysisResultView = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50">
      <HeaderNav />
      
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white/90 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-purple-100">
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-3xl font-bold">
                <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  Job Analysis Results ✨
                </span>
              </h2>
              <button
                onClick={() => setCurrentView('dashboard')}
                className="text-purple-600 hover:text-purple-800 font-medium"
              >
                ← Back to Dashboard
              </button>
            </div>

            {analysisResult && (
              <div className="space-y-8">
                <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-6 rounded-3xl text-white">
                  <h3 className="font-bold text-xl mb-4 flex items-center">
                    <span className="mr-3">🎯</span>
                    Match Score
                  </h3>
                  <div className="flex items-center">
                    <div className="w-full bg-white/30 rounded-full h-4">
                      <div 
                        className="bg-white h-4 rounded-full transition-all duration-1000" 
                        style={{width: `${analysisResult.match_score * 100}%`}}
                      ></div>
                    </div>
                    <span className="ml-4 text-white font-bold text-2xl">
                      {Math.round(analysisResult.match_score * 100)}%
                    </span>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-blue-50 to-purple-50 p-6 rounded-3xl border border-blue-200">
                  <h3 className="font-bold text-xl mb-4 flex items-center text-blue-800">
                    <span className="mr-3">📊</span>
                    Job Analysis
                  </h3>
                  <div className="bg-white/80 backdrop-blur-sm p-4 rounded-2xl">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700">
                      {typeof analysisResult.analysis === 'object' 
                        ? JSON.stringify(analysisResult.analysis, null, 2)
                        : analysisResult.analysis
                      }
                    </pre>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-3xl border border-green-200">
                  <h3 className="font-bold text-xl mb-4 flex items-center text-green-800">
                    <span className="mr-3">💡</span>
                    Recommendations
                  </h3>
                  <div className="bg-white/80 backdrop-blur-sm p-4 rounded-2xl">
                    <div className="text-sm text-gray-700 whitespace-pre-wrap">
                      {Array.isArray(analysisResult.recommendations) 
                        ? analysisResult.recommendations.join('\n\n')
                        : analysisResult.recommendations
                      }
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-gray-50 to-slate-50 p-6 rounded-3xl border border-gray-200">
                  <h3 className="font-bold text-xl mb-4 flex items-center text-gray-800">
                    <span className="mr-3">📝</span>
                    Original Job Description
                  </h3>
                  <div className="bg-white/80 backdrop-blur-sm p-4 rounded-2xl">
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
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50">
      <HeaderNav />
      
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white/90 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-pink-100">
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-3xl font-bold">
                <span className="bg-gradient-to-r from-pink-600 to-purple-600 bg-clip-text text-transparent">
                  Career Advice ✨
                </span>
              </h2>
              <button
                onClick={() => setCurrentView('dashboard')}
                className="text-pink-600 hover:text-pink-800 font-medium"
              >
                ← Back to Dashboard
              </button>
            </div>

            {careerAdvice && (
              <div className="space-y-8">
                <div className="bg-gradient-to-r from-pink-500 to-purple-500 p-6 rounded-3xl text-white">
                  <h3 className="font-bold text-xl mb-4 flex items-center">
                    <span className="mr-3">❓</span>
                    Your Question
                  </h3>
                  <p className="text-pink-100 text-lg">{careerAdvice.query}</p>
                </div>

                <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-3xl border border-green-200">
                  <h3 className="font-bold text-xl mb-4 flex items-center text-green-800">
                    <span className="mr-3">💡</span>
                    AI Career Advice
                  </h3>
                  <div className="bg-white/80 backdrop-blur-sm p-4 rounded-2xl">
                    <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
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
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-indigo-50">
      <HeaderNav />
      
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white/90 backdrop-blur-sm rounded-3xl shadow-2xl p-8 border border-purple-100">
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-3xl font-bold">
                <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                  Career Search Results ✨
                </span>
              </h2>
              <button
                onClick={() => setCurrentView('home')}
                className="text-purple-600 hover:text-purple-800 font-medium"
              >
                ← Back to Home
              </button>
            </div>

            {searchResult && (
              <div className="space-y-8">
                <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-6 rounded-3xl text-white">
                  <h3 className="font-bold text-xl mb-4 flex items-center">
                    <span className="mr-3">🔍</span>
                    Your Search
                  </h3>
                  <p className="text-purple-100 font-medium text-lg">{searchResult.query}</p>
                  <p className="text-sm text-purple-200 mt-2">
                    Search Type: {searchResult.search_type.replace('_', ' ').toUpperCase()}
                  </p>
                </div>

                <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-3xl border border-green-200">
                  <h3 className="font-bold text-xl mb-4 flex items-center text-green-800">
                    <span className="mr-3">💡</span>
                    AI Career Guidance
                  </h3>
                  <div className="bg-white/80 backdrop-blur-sm p-4 rounded-2xl">
                    <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                      {searchResult.response}
                    </div>
                  </div>
                </div>

                {searchResult.suggestions && searchResult.suggestions.length > 0 && (
                  <div className="bg-gradient-to-br from-indigo-50 to-purple-50 p-6 rounded-3xl border border-indigo-200">
                    <h3 className="font-bold text-xl mb-4 flex items-center text-indigo-800">
                      <span className="mr-3">🎯</span>
                      Related Topics
                    </h3>
                    <p className="text-sm text-gray-600 mb-4">You might also be interested in:</p>
                    <div className="space-y-3">
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
                          className="block w-full text-left text-sm bg-white/80 backdrop-blur-sm text-indigo-700 hover:text-indigo-900 hover:bg-indigo-100 px-4 py-3 rounded-2xl transition-all transform hover:scale-105"
                        >
                          <span className="mr-2">🌟</span>
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <div className="text-center pt-8 border-t border-purple-200">
                  <p className="text-gray-600 mb-6 text-lg">Want even more personalized advice?</p>
                  <button
                    onClick={() => setCurrentView('create-profile')}
                    className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-8 py-4 rounded-2xl font-bold text-lg transition-all transform hover:scale-105 shadow-2xl"
                  >
                    <span className="mr-2">👤</span>
                    Create Profile for Personalized Magic
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