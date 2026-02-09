'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Task, TaskPriority, TaskRecurrence } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { z } from 'zod';
import { Loader2, X } from 'lucide-react';

const taskSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200, 'Title must be less than 200 characters'),
  description: z.string().max(2000, 'Description must be less than 2000 characters').optional(),
  dueDate: z.string().optional(),
  tagInput: z.string().optional(),
});

type TaskFormValues = z.infer<typeof taskSchema>;

export interface TaskFormData {
  title: string;
  description?: string | undefined;
  priority?: TaskPriority | undefined;
  dueDate?: string | null | undefined;
  tags?: string[] | null | undefined;
  recurrence?: TaskRecurrence | undefined;
}

interface TaskFormProps {
  task?: Task | undefined;
  onSubmit: (data: TaskFormData) => void;
  onCancel: () => void;
  isSubmitting?: boolean | undefined;
}

// Convert ISO datetime to local datetime-local input value
function toLocalDatetime(isoString: string | null | undefined): string {
  if (!isoString) return '';
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return '';
  // Format as YYYY-MM-DDTHH:mm for datetime-local input
  const pad = (n: number) => n.toString().padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export default function TaskForm({ task, onSubmit, onCancel, isSubmitting }: TaskFormProps) {
  const [priority, setPriority] = useState<TaskPriority>(task?.priority ?? 'medium');
  const [recurrence, setRecurrence] = useState<TaskRecurrence>(task?.recurrence ?? 'none');
  const [tags, setTags] = useState<string[]>(task?.tags ?? []);
  const [tagInput, setTagInput] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TaskFormValues>({
    resolver: zodResolver(taskSchema),
    defaultValues: {
      title: task?.title || '',
      description: task?.description || '',
      dueDate: toLocalDatetime(task?.dueDate),
    },
  });

  const handleAddTag = () => {
    const raw = tagInput.trim().toLowerCase();
    if (!raw) return;
    // Split by commas so users can paste "work, urgent, review"
    const newTags = raw.split(',').map(t => t.trim()).filter(t => t.length > 0 && t.length <= 50);
    const merged = [...tags];
    for (const t of newTags) {
      if (!merged.includes(t) && merged.length < 10) {
        merged.push(t);
      }
    }
    setTags(merged);
    setTagInput('');
  };

  const handleTagKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      handleAddTag();
    }
  };

  const removeTag = (tag: string) => {
    setTags(prev => prev.filter(t => t !== tag));
  };

  const handleFormSubmit = (data: TaskFormValues) => {
    onSubmit({
      title: data.title,
      description: data.description,
      priority,
      dueDate: data.dueDate || null,
      tags: tags.length > 0 ? tags : null,
      recurrence,
    });
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-5">
      {/* Title */}
      <div className="space-y-2">
        <label htmlFor="title" className="block text-sm font-medium text-zinc-300">
          Title <span className="text-red-400">*</span>
        </label>
        <Input
          id="title"
          {...register('title')}
          placeholder="Enter task title"
          className={errors.title ? 'border-red-500/50 focus-visible:ring-red-500/50' : ''}
        />
        {errors.title && (
          <p className="text-xs text-red-400">{errors.title.message}</p>
        )}
      </div>

      {/* Description */}
      <div className="space-y-2">
        <label htmlFor="description" className="block text-sm font-medium text-zinc-300">
          Description
        </label>
        <Textarea
          id="description"
          {...register('description')}
          placeholder="Enter task description (optional)"
          className={errors.description ? 'border-red-500/50 focus-visible:ring-red-500/50' : ''}
        />
        {errors.description && (
          <p className="text-xs text-red-400">{errors.description.message}</p>
        )}
      </div>

      {/* Priority & Due Date row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Priority */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-zinc-300">Priority</label>
          <Select value={priority} onValueChange={(v) => setPriority(v as TaskPriority)}>
            <SelectTrigger>
              <SelectValue placeholder="Select priority" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Due Date */}
        <div className="space-y-2">
          <label htmlFor="dueDate" className="block text-sm font-medium text-zinc-300">Due Date</label>
          <input
            id="dueDate"
            type="datetime-local"
            {...register('dueDate')}
            className="flex h-10 w-full rounded-lg border border-zinc-800 bg-zinc-900/80 px-3 py-2 text-sm text-zinc-200 transition-all duration-200 hover:border-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 [color-scheme:dark]"
          />
        </div>
      </div>

      {/* Recurrence */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-zinc-300">Recurrence</label>
        <Select value={recurrence} onValueChange={(v) => setRecurrence(v as TaskRecurrence)}>
          <SelectTrigger>
            <SelectValue placeholder="Select recurrence" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">None</SelectItem>
            <SelectItem value="daily">Daily</SelectItem>
            <SelectItem value="weekly">Weekly</SelectItem>
            <SelectItem value="monthly">Monthly</SelectItem>
            <SelectItem value="yearly">Yearly</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Tags */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-zinc-300">Tags</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleTagKeyDown}
            onBlur={handleAddTag}
            placeholder="Add tags (comma-separated)"
            className="flex h-10 flex-1 rounded-lg border border-zinc-800 bg-zinc-900/80 px-3 py-2 text-sm text-zinc-200 transition-all duration-200 hover:border-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
          />
          <Button type="button" variant="secondary" size="sm" onClick={handleAddTag} className="h-10 px-3">
            Add
          </Button>
        </div>
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {tags.map(tag => (
              <Badge key={tag} variant="secondary" className="gap-1 pr-1">
                {tag}
                <button
                  type="button"
                  onClick={() => removeTag(tag)}
                  className="ml-0.5 rounded-full p-0.5 hover:bg-zinc-600/50 transition-colors"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        )}
        {tags.length >= 10 && (
          <p className="text-xs text-amber-400">Maximum 10 tags reached</p>
        )}
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-2 pt-4 border-t border-zinc-800/40">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : task ? (
            'Update Task'
          ) : (
            'Create Task'
          )}
        </Button>
      </div>
    </form>
  );
}
