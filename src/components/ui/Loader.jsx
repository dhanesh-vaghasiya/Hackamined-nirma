import "./Loader.css";

const Loader = ({ size = 40 }) => {
  return (
    <div className="loader-wrapper">
      <div
        className="loader"
        style={{ width: size, height: size }}
      />
    </div>
  );
};

export default Loader;
