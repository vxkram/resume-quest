import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

const SummaryPage = () => {
  const { fileName } = useParams();  
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const response = await fetch(`http://localhost:8000/upload/summary/${fileName}/`, {
          method: 'GET',
        });

        if (response.ok) {
          const data = await response.json();
          // Remove **Summary:** if present
          let cleanSummary = data.summary;
          if (cleanSummary.startsWith('**Summary:**')) {
            cleanSummary = cleanSummary.replace('**Summary:**', '').trim();
          }
          setSummary(cleanSummary); 
        } else {
          const errorData = await response.json();
          setError(errorData.error || 'Error fetching summary');
        }
      } catch (error) {
        setError('Error fetching summary');
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [fileName]);

  return (
    <div style={styles.pageContainer}>
      <div style={styles.container}>
        <h2>Resume Summary</h2>
        {loading ? (
          <p>Loading...</p>
        ) : error ? (
          <p style={{ color: 'red' }}>{error}</p>
        ) : (
          <div style={styles.summaryBox}>
            <p>{summary}</p>
          </div>
        )}
        <button onClick={() => navigate(`/questions/${fileName}`)} style={styles.button}>
          Go to Questions Page
        </button>
      </div>
    </div>
  );
};

const styles = {
  pageContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '100vh', 
    backgroundImage: `url(${process.env.PUBLIC_URL + '/image.png'})`, 
    backgroundSize: 'cover',
    backgroundPosition: 'center',
  },
  container: {
    backgroundColor: 'rgba(255, 255, 255, 0.9)', 
    padding: '40px',
    borderRadius: '10px',
    boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
    textAlign: 'center',
    width: '600px', 
    fontFamily: 'Arial, sans-serif',
    color: 'black',
  },
  summaryBox: {
    backgroundColor: 'rgba(240, 240, 240, 0.9)',
    padding: '20px',
    borderRadius: '8px',
    margin: '20px 0',
    textAlign: 'left',
    fontSize: '16px',
    fontFamily: 'Arial, sans-serif',
  },
  button: {
    padding: '10px 20px',
    fontSize: '16px',
    backgroundColor: '#007BFF',
    color: 'white',
    border: 'none',
    cursor: 'pointer',
    marginTop: '20px',
  },
};

export default SummaryPage;
