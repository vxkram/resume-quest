// src/App.js
import React, { useState } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import UploadPage from './components/UploadPage';
import SummaryPage from './components/SummaryPage';
import QuestionsPage from './components/QuestionsPage';

const App = () => {
  const [theme, setTheme] = useState('light'); 

  const toggleTheme = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const isDarkMode = theme === 'dark';

  return (
    <Router>
      <div style={styles.pageContainer(isDarkMode)}>
        <Routes>
          <Route path="/" element={<UploadPage isDarkMode={isDarkMode} />} />
          <Route path="/summary/:fileName" element={<SummaryPage />} /> {}
          <Route path="/questions/:fileName" element={<QuestionsPage />} />{}
        </Routes>
        <button onClick={toggleTheme} style={styles.toggleButton(isDarkMode)}>
          {isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        </button>
      </div>
    </Router>
  );
};



const styles = {
  pageContainer: (isDarkMode) => ({
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    width: '100vw', 
    backgroundColor: isDarkMode ? '#333' : '#f0f0f0',
    backgroundImage: `url(${process.env.PUBLIC_URL + (isDarkMode ? '/night.jpg' : '/day.jpg')})`, 
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    margin: 0, 
    padding: 0, 
  }),
  toggleButton: (isDarkMode) => ({
    position: 'fixed',
    bottom: '20px',
    left: '20px',
    padding: '10px',
    backgroundColor: isDarkMode ? '#D3D3D3' : '#333',
    color: (isDarkMode ? 'black' : 'white'),
    border: 'none',
    cursor: 'pointer',
  }),
};


document.body.style.margin = 0;
document.body.style.padding = 0;

export default App;
