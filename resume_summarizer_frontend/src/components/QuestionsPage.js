import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

const QuestionsPage = () => {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState([]); 
  const [error, setError] = useState('');
  const { fileName } = useParams();  
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch the questions from the backend
    // const fetchQuestions = async () => {
    //   try {
    //     const response = await fetch(`http://localhost:8000/upload/questions/${fileName}`);
    //     if (!response.ok) {
    //       throw new Error('Error fetching questions');
    //     }
    //     const data = await response.json();
    //     setQuestions(data.questions);  
    //     setAnswers(data.user_answers.answers_to_questions || []);  
    //   } catch (err) {
    //     setError('Error fetching questions');
    //   }
    // };

    const fetchQuestions = async () => {
        try {
          const response = await fetch(`http://localhost:8000/upload/questions/${fileName}.json`);
          if (!response.ok) {
            throw new Error('Error fetching questions');
          }
          const data = await response.json();
          console.log(data); 
          setQuestions(data.questions || []); 
          setAnswers(data.user_answers?.answers_to_questions || []); 
        } catch (err) {
          console.error(err); 
          setError('Error fetching questions');
        }
      };
      

    fetchQuestions();
  }, [fileName]);

  
  const handleAnswerChange = (index, value) => {
    const newAnswers = [...answers];
    newAnswers[index] = value;
    setAnswers(newAnswers);
  };

  
  const handleSubmit = async () => {
    try {
      const response = await fetch(`http://localhost:8000/upload/save-answers/${fileName}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ answers }),
      });

      if (response.ok) {
        alert('Answers saved successfully!');
        navigate('/');  
      } else {
        throw new Error('Error saving answers');
      }
    } catch (err) {
      setError('Error saving answers');
    }
  };

  return (
    <div style={styles.pageContainer}>
      <div style={styles.container}>
        <h2>Interview Questions</h2>
        {error && <p style={styles.error}>{error}</p>}
        <div style={styles.questionsContainer}>
          {questions.length > 0 ? (
            <ol>
              {questions.map((question, index) => (
                <li key={index} style={styles.question}>
                  {question.replace(/^\d+\.\s*/, '')} {/* Removing extra numbers here */}
                  <input
                    type="text"
                    value={answers[index] || ""}
                    onChange={(e) => handleAnswerChange(index, e.target.value)}
                    placeholder="Your answer"
                    style={styles.input}
                  />
                </li>
              ))}
            </ol>
          ) : (
            <p>No questions available</p>
          )}
        </div>
        {/* submit button */}
        <button onClick={handleSubmit} style={styles.button}>
          Submit Answers
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
    padding: '30px',
    borderRadius: '15px',
    boxShadow: '0 8px 16px rgba(0, 0, 0, 0.2)',
    textAlign: 'center',
    width: '900px', 
    fontFamily: 'Arial, sans-serif',
    maxWidth: '90%', 
  },
  button: {
    padding: '15px 25px',
    fontSize: '16px',
    backgroundColor: '#007BFF',
    color: 'white',
    border: 'none',
    cursor: 'pointer',
    marginTop: '20px',
  },
  questionsContainer: {
    marginTop: '30px',
    textAlign: 'left',
  },
  question: {
    marginBottom: '15px',
    fontSize: '16px', 
  },
  input: {
    marginTop: '8px',
    padding: '10px',
    width: '100%',
    borderRadius: '8px',
    border: '1px solid #ccc',
    fontSize: '14px',
  },
  error: {
    color: 'red',
    fontSize: '16px',
    marginBottom: '10px',
  },
};

export default QuestionsPage;
