import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom'; // Import useNavigate

const UploadPage = ({ isDarkMode }) => {
  const [file, setFile] = useState(null);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const navigate = useNavigate(); // Initialize useNavigate for navigation

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError('');
    } else {
      setFile(null);
      setError('Please upload a PDF file');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('No PDF selected');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload/', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setSuccessMessage(data.message);
        setError('');
        const fileName = file.name.split('.')[0]; // Extract the file name without extension
        // Navigate to the Summary Page with the file name as a parameter
        navigate(`/summary/${fileName}`);
      } else {
        setError(data.error || 'Something went wrong');
      }
    } catch (error) {
      setError('Failed to upload file. Please try again later.');
    }
  };

  return (
    <div style={styles.container(isDarkMode)}>
      <h2>Upload Your Resume</h2>
      <form onSubmit={handleSubmit} style={styles.form}>
        <label style={styles.label}>Choose a PDF:</label>
        <div style={styles.inputGroup}>
          <label htmlFor="fileInput" style={styles.customFileButton}>Choose PDF</label>
          <input
            id="fileInput"
            type="file"
            onChange={handleFileChange}
            accept="application/pdf"
            style={styles.hiddenInput}
          />
          <span style={styles.placeholder}>
            {file ? file.name : 'No PDFs selected'}
          </span>
          <button type="submit" style={styles.button(isDarkMode)} disabled={!file}>
            Upload Resume
          </button>
        </div>
        {error && <p style={styles.error}>{error}</p>}
        {successMessage && <p style={styles.success}>{successMessage}</p>}
      </form>
    </div>
  );
};

const styles = {
  container: (isDarkMode) => ({
    backgroundColor: isDarkMode ? 'rgba(50, 50, 50, 0.9)' : 'rgba(255, 255, 255, 0.8)',
    padding: '30px',
    borderRadius: '10px',
    boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
    textAlign: 'center',
    width: '400px',
    fontFamily: 'Arial, sans-serif',
    color: isDarkMode ? 'white' : 'black',
  }),
  form: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    marginBottom: '20px',
  },
  customFileButton: {
    padding: '10px 20px',
    backgroundColor: '#007BFF',
    color: 'white',
    border: 'none',
    cursor: 'pointer',
    marginBottom: '10px',
  },
  hiddenInput: {
    display: 'none',
  },
  placeholder: {
    fontSize: '14px',
    color: '#777',
    marginBottom: '10px',
  },
  button: (isDarkMode) => ({
    padding: '10px 20px',
    fontSize: '16px',
    backgroundColor: '#007BFF',
    color: 'white',
    border: 'none',
    cursor: 'pointer',
  }),
  error: {
    color: 'red',
    fontSize: '14px',
    marginBottom: '10px',
  },
  success: {
    color: 'green',
    fontSize: '14px',
    marginBottom: '10px',
  },
};

export default UploadPage;
