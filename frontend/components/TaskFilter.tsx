import React from 'react';
import { TaskPriority } from '@/lib/api';

interface TaskFilterProps {
  filter: 'all' | 'pending' | 'completed';
  onFilterChange: (filter: 'all' | 'pending' | 'completed') => void;
  priorityFilter: 'all' | TaskPriority;
  onPriorityFilterChange: (priority: 'all' | TaskPriority) => void;
}

const statusFilters = [
  { value: 'all' as const, label: 'All' },
  { value: 'pending' as const, label: 'Pending' },
  { value: 'completed' as const, label: 'Completed' },
];

const priorityFilters = [
  { value: 'all' as const, label: 'All Priorities' },
  { value: 'high' as const, label: 'High' },
  { value: 'medium' as const, label: 'Medium' },
  { value: 'low' as const, label: 'Low' },
];

const TaskFilter: React.FC<TaskFilterProps> = ({ filter, onFilterChange, priorityFilter, onPriorityFilterChange }) => {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Status filter */}
      <div className="inline-flex items-center rounded-lg bg-zinc-900/60 border border-zinc-800/60 p-1 gap-1">
        {statusFilters.map((f) => (
          <button
            key={f.value}
            onClick={() => onFilterChange(f.value)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${
              filter === f.value
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/20'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-800/60'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Priority filter */}
      <div className="inline-flex items-center rounded-lg bg-zinc-900/60 border border-zinc-800/60 p-1 gap-1">
        {priorityFilters.map((f) => (
          <button
            key={f.value}
            onClick={() => onPriorityFilterChange(f.value)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${
              priorityFilter === f.value
                ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-500/20'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-800/60'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>
    </div>
  );
};

export default TaskFilter;
