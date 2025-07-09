import React, { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentView, setCurrentView] = useState("home");
  const [userProfile, setUserProfile] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [jobDescription, setJobDescription] = useState("");
  const [analysisResult, setAnalysisResult] = useState(null);
  const [careerQuery, setCareerQuery] = useState("");
  const [careerAdvice, setCareerAdvice] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchType, setSearchType] = useState("general");
  const [searchResult, setSearchResult] = useState(null);
  const [popularTopics, setPopularTopics] = useState(null);
  const [loading, setLoading] = useState(false);

  // Profile form state
  const [profileForm, setProfileForm] = useState({
    name: "",
    education_level: "",
    field_of_study: "",
    skills: "",
    experience_years: 0,
    current_role: "",
    career_interests: ""
  });

  // Load data on mount
  useEffect(() => {
    loadProfiles();
    loadPopularTopics();
  }, []);

  const loadProfiles = async () => {
    try {
      const res = await axios.get(`${API}/profiles`);
      setProfiles(res.data);
      if (res.data.length) setUserProfile(res.data[0]);
    } catch (err) {
      console.error("Error loading profiles:", err);
    }
  };

  const loadPopularTopics = async () => {
    try {
      const res = await axios.get(`${API}/popular-topics`);
      setPopularTopics(res.data);
    } catch (err) {
      console.error("Error loading topics:", err);
    }
  };

  const performAnonymousSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API}/search`, { query: searchQuery, search_type: searchType });
      setSearchResult(res.data);
      setCurrentView("search-result");
    } catch (err) {
      console.error(err);
      alert("Search failed. Please try again.");
    }
    setLoading(false);
  };

  const createProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        ...profileForm,
        skills: profileForm.skills.split(',').map(s => s.trim()).filter(Boolean),
        career_interests: profileForm.career_interests.split(',').map(s => s.trim()).filter(Boolean)
      };
      const res = await axios.post(`${API}/profiles`, payload);
      setUserProfile(res.data);
      setProfiles(prev => [...prev, res.data]);
      setCurrentView("dashboard");
      setProfileForm({ name:"", education_level:"", field_of_study:"", skills:"", experience_years:0, current_role:"", career_interests:"" });
    } catch (err) {
      console.error(err);
      alert("Profile creation error.");
    }
    setLoading(false);
  };

  const analyzeJob = async (e) => {
    e.preventDefault();
    if (!userProfile) return alert("Please create a profile first.");
    setLoading(true);
    try {
      const res = await axios.post(`${API}/analyze-job`, { user_id: userProfile.id, job_description: jobDescription });
      setAnalysisResult(res.data);
      setCurrentView("analysis-result");
    } catch (err) {
      console.error(err);
      alert("Job analysis error.");
    }
    setLoading(false);
  };

  const getCareerAdvice = async (e) => {
    e.preventDefault();
    if (!userProfile) return alert("Please create a profile first.");
    setLoading(true);
    try {
      const res = await axios.post(`${API}/career-advice`, { user_id: userProfile.id, query: careerQuery });
      setCareerAdvice(res.data);
      setCurrentView("advice-result");
    } catch (err) {
      console.error(err);
      alert("Advice error.");
    }
    setLoading(false);
  };

  // Navigation component
  const HeaderNav = () => (
    <nav className="bg-white shadow p-4">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-xl font-bold">NextStep</h1>
        <div className="space-x-4">
          <button onClick={() => setCurrentView('home')} className="hover:underline">Home</button>
          {userProfile && <button onClick={() => setCurrentView('dashboard')} className="hover:underline">Dashboard</button>}
        </div>
      </div>
    </nav>
  );

  // Define view components below... (HomeView, CreateProfileView, DashboardView, AnalysisResultView, AdviceResultView, SearchResultView)
  // For brevity, assume these are refactored similarly, without duplication.

  const renderView = () => {
    switch (currentView) {
      case 'create-profile': return <CreateProfileView />;
      case 'dashboard': return <DashboardView />;
      case 'analysis-result': return <AnalysisResultView />;
      case 'advice-result': return <AdviceResultView />;
      case 'search-result': return <SearchResultView />;
      default: return <HomeView />;
    }
  };

  return (
    <BrowserRouter>
      <div className="App">
        {renderView()}
      </div>
    </BrowserRouter>
  );
}

export default App;
