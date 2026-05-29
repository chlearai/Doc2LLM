import type { InputHTMLAttributes } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
  error?: string;
  reserveHintSpace?: boolean;
};

export function Input({ label, hint, error, reserveHintSpace = false, id, className = "", ...props }: InputProps) {
  const inputId = id ?? props.name;
  return (
    <label className={`field ${className}`.trim()} htmlFor={inputId}>
      <span className="field-label">{label}</span>
      <input id={inputId} className="input" aria-invalid={Boolean(error)} {...props} />
      {error ? <span className="field-error">{error}</span> : null}
      {!error && hint ? <span className="field-hint">{hint}</span> : null}
      {!error && !hint && reserveHintSpace ? <span className="field-hint" aria-hidden="true">&nbsp;</span> : null}
    </label>
  );
}
