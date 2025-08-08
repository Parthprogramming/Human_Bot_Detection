import logo from './logo.svg';
import './App.css';
import Verification from "./components/captcha-form";
import Http_bot from "./components/http_client_verification";
import Auth_used from "./components/auth_user";
import Sign_in from "./components/sign-in";
import Sign_up from "./components/sign-up";
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Verification />} />
        <Route path="/http-bot-check" element={<Http_bot />} />
        <Route path="/auth-user" element={<Auth_used />} />
        <Route path="/sign-in" element={<Sign_in />} />
        <Route path="/sign-up" element={<Sign_up />} />
      </Routes>
    </Router>
  );
}

export default App;
