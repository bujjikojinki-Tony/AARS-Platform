type WeaknessListPanelProps = {
  weaknesses: string[];
};

export function WeaknessListPanel({ weaknesses }: WeaknessListPanelProps) {
  return (
    <section className="card weakness-card" aria-labelledby="weakness-list-title">
      <div className="card-header">
        <div className="section-label">Weakness List Panel</div>
        <h2 className="card-title" id="weakness-list-title">
          Main weaknesses / risks
        </h2>
      </div>

      <div className="result-summary-block">
        <div className="timeline-list">
          {weaknesses.map((item) => (
            <div className="timeline-item" key={item}>
              <div className="timeline-title">{item}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
