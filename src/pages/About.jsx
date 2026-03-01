import Card from "../components/ui/Card";

const About = () => {
  return (
    <div className="page">
      <h1>About</h1>
      <Card>
        <p style={{ lineHeight: 1.7, color: "var(--color-text-secondary)" }}>
          This is a starter React application scaffolded with Vite. It includes
          routing, authentication context, theme switching, reusable UI
          components, and a clean project structure ready for you to build upon.
        </p>
      </Card>
    </div>
  );
};

export default About;
