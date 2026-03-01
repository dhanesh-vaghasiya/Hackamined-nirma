import { Link } from "react-router-dom";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import "./Home.css";

const Home = () => {
  return (
    <div className="page home-page">
      <section className="hero">
        <h1>Welcome to MyApp</h1>
        <p className="hero-subtitle">
          A modern, clean starter template for building amazing applications.
        </p>
        <div className="hero-actions">
          <Link to="/register">
            <Button variant="primary" size="lg">
              Get Started
            </Button>
          </Link>
          <Link to="/about">
            <Button variant="outline" size="lg">
              Learn More
            </Button>
          </Link>
        </div>
      </section>

      <section className="features">
        <h2>Features</h2>
        <div className="features-grid">
          <Card>
            <h3>Fast & Modern</h3>
            <p>Built with React and Vite for lightning-fast development.</p>
          </Card>
          <Card>
            <h3>Responsive</h3>
            <p>Looks great on any device, from mobile to desktop.</p>
          </Card>
          <Card>
            <h3>Customizable</h3>
            <p>Easy to extend and tailor to your specific needs.</p>
          </Card>
        </div>
      </section>
    </div>
  );
};

export default Home;
