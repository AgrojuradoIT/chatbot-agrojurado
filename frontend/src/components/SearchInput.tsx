import React from 'react';
import '../styles/SearchInput.css';

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  resultsCount?: number;
  totalCount?: number;
  className?: string;
  showResultsInfo?: boolean;
  showClearButton?: boolean;
  disabled?: boolean;
}

const SearchInput: React.FC<SearchInputProps> = ({
  value,
  onChange,
  placeholder,
  resultsCount,
  totalCount,
  className = '',
  showResultsInfo = true,
  showClearButton = true,
  disabled = false
}) => {
  return (
    <div className={`search-container ${className}`}>
      <div className="search-input-wrapper">
        <span className="material-icons search-icon">search</span>
        <input
          type="text"
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="search-input"
          disabled={disabled}
        />
        {showClearButton && value && (
          <button
            className="clear-search-btn"
            onClick={() => onChange('')}
            title="Limpiar búsqueda"
            disabled={disabled}
          >
            <span className="material-icons">close</span>
          </button>
        )}
      </div>
      {showResultsInfo && value && resultsCount !== undefined && totalCount !== undefined && (
        <div className="search-results-info">
          {resultsCount} de {totalCount} encontrados
        </div>
      )}
    </div>
  );
};

export default SearchInput; 
