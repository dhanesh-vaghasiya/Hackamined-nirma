const companies = ["TATA Bank", "TATA", "Altrasindia", "STARA", "METNP"];

const TrustedRow = () => {
  return (
    <section className="mt-7">
      <p className="font-data text-[11px] uppercase tracking-[0.18em] text-[#9ba69a]">
        TRUSTED BY LEADERS ACROSS INDIA
      </p>
      <div className="mt-5 flex flex-wrap items-center gap-x-10 gap-y-4 text-[15px] font-semibold text-[#7c857c]">
        {companies.map((company) => (
          <span key={company} className="tracking-wide opacity-95 grayscale transition-opacity duration-200 hover:opacity-100">
            {company}
          </span>
        ))}
      </div>
    </section>
  );
};

export default TrustedRow;
