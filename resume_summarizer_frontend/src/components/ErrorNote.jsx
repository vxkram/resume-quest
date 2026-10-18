export function ErrorNote({ error }) {
  if (!error) return null;
  return (
    <p className="error" role="alert">
      {error.message ?? String(error)}
    </p>
  );
}
