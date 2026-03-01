import { Link } from "react-router-dom";
import Button from "../components/ui/Button";

const NotFound = () => {
  return (
    <div className="page" style={{ textAlign: "center", paddingTop: "6rem" }}>
      <h1 style={{ fontSize: "5rem", marginBottom: "0.5rem", opacity: 0.3 }}>
        404
      </h1>
      <h2>Page Not Found</h2>
      <p style={{ color: "var(--color-text-secondary)", margin: "1rem 0 2rem" }}>
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Link to="/">
        <Button variant="primary">Go Home</Button>
      </Link>
    </div>
  );
};

export default NotFound;
