import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the resume upload page by default', () => {
  render(<App />);
  expect(screen.getByText(/upload your resume/i)).toBeInTheDocument();
});

test('renders a theme toggle button', () => {
  render(<App />);
  expect(screen.getByText(/switch to dark mode/i)).toBeInTheDocument();
});
