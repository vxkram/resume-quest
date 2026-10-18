import { useEffect, useState } from "react";
import { BrowserRouter, Link, Route, Routes, useLocation } from "react-router";

import { Sprite } from "./components/Sprite";
import { Window } from "./components/Window";
import { Interview } from "./screens/Interview";
import { Quiz } from "./screens/Quiz";
import { Saves } from "./screens/Saves";
import { Sheet } from "./screens/Sheet";
import { Title } from "./screens/Title";
import { Training } from "./screens/Training";
import { SessionProvider } from "./session";

const THEME = "resume-quest:theme";

function useTheme() {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem(THEME);
    } catch {
      return null;
    }
  });
  useEffect(() => {
    const root = document.documentElement;
    if (theme) root.dataset.theme = theme;
    else delete root.dataset.theme;
    try {
      if (theme) localStorage.setItem(THEME, theme);
    } catch {
      // Storage blocked: the choice lasts until reload.
    }
  }, [theme]);
  const isNight = theme ? theme === "dark" : window.matchMedia?.("(prefers-color-scheme: dark)").matches;
  return [isNight, () => setTheme(isNight ? "light" : "dark")];
}

function Sky() {
  return (
    <div className="sky" aria-hidden="true">
      <Sprite name="cloud" scale={6} className="cloud cloud-a" />
      <Sprite name="cloud" scale={4} className="cloud cloud-b" />
      <Sprite name="cloud" scale={5} className="cloud cloud-c" />
    </div>
  );
}

export function Shell({ children }) {
  const [isNight, toggle] = useTheme();
  const onTitle = useLocation().pathname === "/";
  return (
    <>
      <Sky />
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header className="topbar">
        {onTitle ? <span /> : (
          <Link to="/" className="brand">
            Résumé Quest
          </Link>
        )}
        <nav className="topnav" aria-label="Main">
          <Link to="/">New game</Link>
          <Link to="/saves">Save files</Link>
          <button type="button" className="btn btn-small" onClick={toggle} aria-label={isNight ? "Switch to day" : "Switch to night"}>
            {isNight ? "Day" : "Night"}
          </button>
        </nav>
      </header>
      <main id="main">{children}</main>
      <footer className="ground">
        <Sprite name="hero" scale={5} className="ground-hero" />
        <p>Runs on your computer. Keys stay in this tab.</p>
      </footer>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <SessionProvider>
        <Shell>
          <Routes>
            <Route path="/" element={<Title />} />
            <Route path="/saves" element={<Saves />} />
            <Route path="/sheet/:id" element={<Sheet />} />
            <Route path="/sheet/:id/quiz" element={<Quiz />} />
            <Route path="/sheet/:id/interview" element={<Interview />} />
            <Route path="/sheet/:id/training" element={<Training />} />
            <Route path="*" element={<Window title="Lost in the woods"><Link to="/">Back to the title screen</Link></Window>} />
          </Routes>
        </Shell>
      </SessionProvider>
    </BrowserRouter>
  );
}
