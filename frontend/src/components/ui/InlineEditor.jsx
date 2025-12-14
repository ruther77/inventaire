/**
 * InlineEditor - Édition in-place pour tables et cards
 * Phase 4 - UX_NEXT_GEN_2025.md
 *
 * Permet d'éditer une valeur directement sans modal ni navigation
 * Support: texte, nombre, select, date
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Check, X, Pencil, Loader2 } from 'lucide-react';
import clsx from 'clsx';

// ============================================================================
// INLINE TEXT EDITOR
// ============================================================================

export function InlineTextEditor({
  value,
  onSave,
  onCancel,
  placeholder = 'Saisir...',
  className,
  inputClassName,
  disabled = false,
  autoFocus = true,
  maxLength,
  minLength,
  pattern,
  required = false,
}) {
  const [editValue, setEditValue] = useState(value || '');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [autoFocus]);

  const handleSave = async () => {
    if (required && !editValue.trim()) {
      setError('Ce champ est requis');
      return;
    }
    if (minLength && editValue.length < minLength) {
      setError(`Minimum ${minLength} caractères`);
      return;
    }
    if (pattern && !new RegExp(pattern).test(editValue)) {
      setError('Format invalide');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      await onSave(editValue);
    } catch (err) {
      setError(err.message || 'Erreur de sauvegarde');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onCancel?.();
    }
  };

  return (
    <div className={clsx('inline-flex items-center gap-1', className)}>
      <input
        ref={inputRef}
        type="text"
        value={editValue}
        onChange={(e) => {
          setEditValue(e.target.value);
          setError(null);
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        maxLength={maxLength}
        disabled={disabled || isLoading}
        className={clsx(
          'px-2 py-1 text-sm rounded border',
          'focus:outline-none focus:ring-2 focus:ring-brand-500/50',
          error
            ? 'border-red-300 bg-red-50'
            : 'border-slate-300 bg-white',
          inputClassName
        )}
      />
      <button
        type="button"
        onClick={handleSave}
        disabled={isLoading}
        className="p-1 rounded hover:bg-emerald-100 text-emerald-600 transition-colors"
        title="Sauvegarder"
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Check className="w-4 h-4" />
        )}
      </button>
      <button
        type="button"
        onClick={onCancel}
        disabled={isLoading}
        className="p-1 rounded hover:bg-red-100 text-red-600 transition-colors"
        title="Annuler"
      >
        <X className="w-4 h-4" />
      </button>
      {error && (
        <span className="text-xs text-red-500 ml-1">{error}</span>
      )}
    </div>
  );
}

// ============================================================================
// INLINE NUMBER EDITOR
// ============================================================================

export function InlineNumberEditor({
  value,
  onSave,
  onCancel,
  placeholder = '0',
  className,
  disabled = false,
  min,
  max,
  step = 1,
  suffix = '',
  prefix = '',
  decimals = 2,
}) {
  const [editValue, setEditValue] = useState(value?.toString() || '');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, []);

  const handleSave = async () => {
    const numValue = parseFloat(editValue);

    if (isNaN(numValue)) {
      setError('Nombre invalide');
      return;
    }
    if (min !== undefined && numValue < min) {
      setError(`Minimum: ${min}`);
      return;
    }
    if (max !== undefined && numValue > max) {
      setError(`Maximum: ${max}`);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      await onSave(parseFloat(numValue.toFixed(decimals)));
    } catch (err) {
      setError(err.message || 'Erreur');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onCancel?.();
    }
  };

  return (
    <div className={clsx('inline-flex items-center gap-1', className)}>
      {prefix && <span className="text-sm text-slate-500">{prefix}</span>}
      <input
        ref={inputRef}
        type="number"
        value={editValue}
        onChange={(e) => {
          setEditValue(e.target.value);
          setError(null);
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        min={min}
        max={max}
        step={step}
        disabled={disabled || isLoading}
        className={clsx(
          'w-24 px-2 py-1 text-sm text-right rounded border',
          'focus:outline-none focus:ring-2 focus:ring-brand-500/50',
          error
            ? 'border-red-300 bg-red-50'
            : 'border-slate-300 bg-white'
        )}
      />
      {suffix && <span className="text-sm text-slate-500">{suffix}</span>}
      <button
        type="button"
        onClick={handleSave}
        disabled={isLoading}
        className="p-1 rounded hover:bg-emerald-100 text-emerald-600 transition-colors"
      >
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Check className="w-4 h-4" />
        )}
      </button>
      <button
        type="button"
        onClick={onCancel}
        disabled={isLoading}
        className="p-1 rounded hover:bg-red-100 text-red-600 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
      {error && (
        <span className="text-xs text-red-500 ml-1">{error}</span>
      )}
    </div>
  );
}

// ============================================================================
// INLINE SELECT EDITOR
// ============================================================================

export function InlineSelectEditor({
  value,
  options = [],
  onSave,
  onCancel,
  placeholder = 'Sélectionner...',
  className,
  disabled = false,
}) {
  const [editValue, setEditValue] = useState(value || '');
  const [isLoading, setIsLoading] = useState(false);
  const selectRef = useRef(null);

  useEffect(() => {
    if (selectRef.current) {
      selectRef.current.focus();
    }
  }, []);

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await onSave(editValue);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = async (e) => {
    const newValue = e.target.value;
    setEditValue(newValue);
    setIsLoading(true);
    try {
      await onSave(newValue);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onCancel?.();
    }
  };

  return (
    <div className={clsx('inline-flex items-center gap-1', className)}>
      <select
        ref={selectRef}
        value={editValue}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled || isLoading}
        className={clsx(
          'px-2 py-1 text-sm rounded border border-slate-300',
          'focus:outline-none focus:ring-2 focus:ring-brand-500/50',
          'bg-white'
        )}
      >
        <option value="">{placeholder}</option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {isLoading && <Loader2 className="w-4 h-4 animate-spin text-slate-400" />}
      <button
        type="button"
        onClick={onCancel}
        disabled={isLoading}
        className="p-1 rounded hover:bg-red-100 text-red-600 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

// ============================================================================
// EDITABLE CELL - Composant wrapper pour affichage/édition
// ============================================================================

export default function EditableCell({
  value,
  displayValue,
  onSave,
  type = 'text',
  editable = true,
  className,
  editClassName,
  options, // pour type='select'
  suffix,
  prefix,
  min,
  max,
  step,
  decimals,
  placeholder,
  formatDisplay, // fonction pour formatter l'affichage
}) {
  const [isEditing, setIsEditing] = useState(false);

  const handleSave = async (newValue) => {
    await onSave?.(newValue);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  // Affichage en mode lecture
  const displayText = formatDisplay
    ? formatDisplay(value)
    : displayValue !== undefined
    ? displayValue
    : value;

  if (isEditing) {
    const commonProps = {
      value,
      onSave: handleSave,
      onCancel: handleCancel,
      className: editClassName,
      placeholder,
    };

    switch (type) {
      case 'number':
        return (
          <InlineNumberEditor
            {...commonProps}
            suffix={suffix}
            prefix={prefix}
            min={min}
            max={max}
            step={step}
            decimals={decimals}
          />
        );
      case 'select':
        return (
          <InlineSelectEditor
            {...commonProps}
            options={options}
          />
        );
      default:
        return <InlineTextEditor {...commonProps} />;
    }
  }

  return (
    <div
      className={clsx(
        'group inline-flex items-center gap-1.5',
        editable && 'cursor-pointer hover:bg-slate-50 rounded px-1 -mx-1',
        className
      )}
      onClick={() => editable && setIsEditing(true)}
      role={editable ? 'button' : undefined}
      tabIndex={editable ? 0 : undefined}
      onKeyDown={(e) => {
        if (editable && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          setIsEditing(true);
        }
      }}
    >
      <span>{displayText || <span className="text-slate-400 italic">-</span>}</span>
      {editable && (
        <Pencil className="w-3 h-3 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
      )}
    </div>
  );
}

// ============================================================================
// INLINE EDITOR ROW - Pour édition de ligne complète
// ============================================================================

export function InlineEditorRow({
  fields,
  data,
  onSave,
  onCancel,
  isNew = false,
  className,
}) {
  const [editData, setEditData] = useState(data || {});
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const handleFieldChange = (fieldName, value) => {
    setEditData((prev) => ({ ...prev, [fieldName]: value }));
    setErrors((prev) => ({ ...prev, [fieldName]: null }));
  };

  const validate = () => {
    const newErrors = {};
    fields.forEach((field) => {
      if (field.required && !editData[field.name]) {
        newErrors[field.name] = 'Requis';
      }
      if (field.validate) {
        const error = field.validate(editData[field.name], editData);
        if (error) newErrors[field.name] = error;
      }
    });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) return;

    setIsLoading(true);
    try {
      await onSave(editData);
    } catch (err) {
      setErrors({ _form: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <tr className={clsx('bg-amber-50/50', className)}>
      {fields.map((field) => (
        <td key={field.name} className="px-3 py-2">
          {field.type === 'select' ? (
            <select
              value={editData[field.name] || ''}
              onChange={(e) => handleFieldChange(field.name, e.target.value)}
              className={clsx(
                'w-full px-2 py-1 text-sm rounded border',
                errors[field.name]
                  ? 'border-red-300'
                  : 'border-slate-300'
              )}
            >
              <option value="">{field.placeholder || 'Sélectionner...'}</option>
              {field.options?.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          ) : field.type === 'number' ? (
            <input
              type="number"
              value={editData[field.name] || ''}
              onChange={(e) => handleFieldChange(field.name, e.target.value)}
              min={field.min}
              max={field.max}
              step={field.step}
              className={clsx(
                'w-full px-2 py-1 text-sm text-right rounded border',
                errors[field.name]
                  ? 'border-red-300'
                  : 'border-slate-300'
              )}
            />
          ) : (
            <input
              type="text"
              value={editData[field.name] || ''}
              onChange={(e) => handleFieldChange(field.name, e.target.value)}
              placeholder={field.placeholder}
              className={clsx(
                'w-full px-2 py-1 text-sm rounded border',
                errors[field.name]
                  ? 'border-red-300'
                  : 'border-slate-300'
              )}
            />
          )}
          {errors[field.name] && (
            <span className="text-xs text-red-500">{errors[field.name]}</span>
          )}
        </td>
      ))}
      <td className="px-3 py-2">
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={handleSave}
            disabled={isLoading}
            className="p-1.5 rounded bg-emerald-500 hover:bg-emerald-600 text-white transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Check className="w-4 h-4" />
            )}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="p-1.5 rounded bg-slate-200 hover:bg-slate-300 text-slate-700 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        {errors._form && (
          <span className="text-xs text-red-500 block mt-1">{errors._form}</span>
        )}
      </td>
    </tr>
  );
}
