const PIPE_STAGES = ["Parse", "Retrieve", "Evaluate", "Tool Calls", "Synthesize", "Validate"];

export default function PipelineBar({ activeStage, doneStages }) {
  return (
    <div className="pipeline">
      {PIPE_STAGES.map((s, i) => {
        const done = doneStages.includes(i);
        const active = activeStage === i;
        return (
          <div key={s} className={`pipe-stage${active ? " active" : done ? " done" : ""}`}>
            <div className="pipe-stage-name">{done ? "\u2713 " : active ? "\u25cf " : ""}{s}</div>
          </div>
        );
      })}
    </div>
  );
}
