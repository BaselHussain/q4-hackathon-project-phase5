import React from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Clock, FileText, Check, RotateCcw, Pencil, Trash2, CalendarClock, Repeat, Tag } from 'lucide-react';
import { Task, TaskPriority } from '@/lib/api';

interface TaskCardProps {
  task: Task;
  onEdit?: (task: Task) => void;
  onDelete?: (id: string) => void;
  onToggleComplete?: (id: string) => void;
}

const priorityConfig: Record<TaskPriority, { label: string; classes: string }> = {
  high: { label: 'High', classes: 'bg-red-500/10 text-red-400 ring-1 ring-red-500/20' },
  medium: { label: 'Medium', classes: 'bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20' },
  low: { label: 'Low', classes: 'bg-blue-500/10 text-blue-400 ring-1 ring-blue-500/20' },
};

const recurrenceLabels: Record<string, string> = {
  daily: 'Daily',
  weekly: 'Weekly',
  monthly: 'Monthly',
  yearly: 'Yearly',
};

const TaskCard: React.FC<TaskCardProps> = ({ task, onEdit, onDelete, onToggleComplete }) => {
  const isCompleted = task.status === 'completed';

  const formatDate = (date: string) => {
    if (!date) return '';
    return new Date(date).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' });
  };

  const formatDueDate = (date: string) => {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const isOverdue = task.dueDate && !isCompleted && new Date(task.dueDate) < new Date();
  const pConfig = priorityConfig[task.priority] || priorityConfig.medium;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      layout
    >
      <div className={`group relative rounded-xl border bg-zinc-900/50 p-5 transition-all duration-200 hover:bg-zinc-900/80 ${
        isCompleted
          ? 'border-emerald-800/30 hover:border-emerald-700/40'
          : 'border-zinc-800/60 hover:border-zinc-700/60'
      }`}>
        {/* Status indicator line */}
        <div className={`absolute left-0 top-4 bottom-4 w-0.5 rounded-full ${
          isCompleted ? 'bg-emerald-500' : isOverdue ? 'bg-red-500' : 'bg-amber-500'
        }`} />

        <div className="pl-3">
          {/* Header */}
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <h3 className={`font-semibold text-base tracking-tight break-words ${
                  isCompleted ? 'text-zinc-400 line-through decoration-zinc-600' : 'text-white'
                }`}>
                  {task.title}
                </h3>
                {/* Priority badge */}
                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${pConfig.classes}`}>
                  {pConfig.label}
                </span>
              </div>
            </div>
            <span className={`shrink-0 inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${
              isCompleted
                ? 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20'
                : 'bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20'
            }`}>
              <div className={`h-1.5 w-1.5 rounded-full ${isCompleted ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              {isCompleted ? 'Done' : 'Pending'}
            </span>
          </div>

          {/* Description */}
          {task.description && (
            <div className="flex items-start gap-2 mb-3">
              <FileText className="h-3.5 w-3.5 mt-0.5 text-zinc-600 shrink-0" />
              <p className="text-sm text-zinc-400 break-words leading-relaxed">{task.description}</p>
            </div>
          )}

          {/* Metadata row: due date, recurrence, tags */}
          {(task.dueDate || (task.recurrence && task.recurrence !== 'none') || (task.tags && task.tags.length > 0)) && (
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 mb-3">
              {/* Due date */}
              {task.dueDate && (
                <span className={`inline-flex items-center gap-1 text-xs ${
                  isOverdue ? 'text-red-400 font-medium' : 'text-zinc-500'
                }`}>
                  <CalendarClock className="h-3 w-3" />
                  {isOverdue && 'Overdue: '}{formatDueDate(task.dueDate)}
                </span>
              )}

              {/* Recurrence */}
              {task.recurrence && task.recurrence !== 'none' && (
                <span className="inline-flex items-center gap-1 text-xs text-violet-400">
                  <Repeat className="h-3 w-3" />
                  {recurrenceLabels[task.recurrence] || task.recurrence}
                </span>
              )}

              {/* Tags */}
              {task.tags && task.tags.length > 0 && (
                <div className="flex items-center gap-1 flex-wrap">
                  <Tag className="h-3 w-3 text-zinc-600" />
                  {task.tags.map(tag => (
                    <Badge key={tag} variant="secondary" className="text-[10px] px-1.5 py-0">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Footer */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mt-4 pt-3 border-t border-zinc-800/40">
            <div className="flex items-center gap-1.5 text-xs text-zinc-600">
              <Clock className="h-3 w-3" />
              <span>{formatDate(task.createdAt)}</span>
            </div>

            <div className="flex items-center gap-1.5">
              <Button variant="ghost" size="sm" onClick={() => onEdit?.(task)} className="text-zinc-500 hover:text-white h-7 px-2">
                <Pencil className="h-3.5 w-3.5" />
              </Button>
              <Button variant="ghost" size="sm" onClick={() => onDelete?.(task.id)} className="text-zinc-500 hover:text-red-400 h-7 px-2">
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
              <Button
                variant={isCompleted ? 'outline' : 'primary'}
                size="sm"
                onClick={() => onToggleComplete?.(task.id)}
                className="h-7 text-xs"
              >
                {isCompleted ? (
                  <><RotateCcw className="h-3 w-3" /> Reopen</>
                ) : (
                  <><Check className="h-3 w-3" /> Complete</>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default TaskCard;
