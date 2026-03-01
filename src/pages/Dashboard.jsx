import { useAuth } from "../context/AuthContext";
import Card from "../components/ui/Card";

const Dashboard = () => {
  const { user } = useAuth();

  return (
    <div className="page">
      <h1>Dashboard</h1>
      <Card>
        <h3>Welcome back{user?.name ? `, ${user.name}` : ""}!</h3>
        <p style={{ color: "var(--color-text-secondary)", marginTop: "0.5rem" }}>
          This is a protected page. Only authenticated users can see this.
        </p>
      </Card>
    </div>
  );
};

export default Dashboard;
