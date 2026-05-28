import type { InputHTMLAttributes } from "react";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
  error?: string;
};

export function Input({ label, hint, error, id, className = "", ...props }: InputProps) {
  const inputId = id ?? props.name;
  return (
    <label className={`field ${className}`.trim()} htmlFor={inputId}>
      <span className="field-label">{label}</span>
      <input id={inputId} className="input" aria-invalid={Boolean(error)} {...props} />
      {error ? <span className="field-error">{error}</span> : null}
      {!error && hint ? <span className="field-hint">{hint}</span> : null}
    </label>
  );
}
