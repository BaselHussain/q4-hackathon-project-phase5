'use client';

import React, { useState } from 'react';
import { AnimatePresence } from 'framer-motion';
import TaskCard from '@/components/TaskCard';
import TaskFilter from '@/components/TaskFilter';
import TaskModal from '@/components/TaskModal';
import { AlertTriangle, RefreshCw, Plus, Inbox } from 'lucide-react';
import { useTasks } from '@/hooks/useTasks';
import { Button } from '@/components/ui/button';
import { Task, TaskPriority } from '@/lib/api';

const TaskList: React.FC = () => {
  const [filter, setFilter] = useState<'all' | 'pending' | 'completed'>('all');
  const [priorityFilter, setPriorityFilter] = useState<'all' | TaskPriority>('all');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | undefined>(undefined);
  const { tasks, loading, error, loadTasks, createTask, updateTask, deleteTask, toggleTaskCompletion } = useTasks();

  const filteredTasks = tasks.filter(task => {
    if (filter !== 'all' && task.status !== filter) return false;
    if (priorityFilter !== 'all' && task.priority !== priorityFilter) return false;
    return true;
  });

  const handleEdit = (task: Task) => {
    setEditingTask(task);
    setIsModalOpen(true);
  };

  const handleDelete = (id: string) => {
    deleteTask(id);
  };

  const handleToggleComplete = (id: string) => {
    toggleTaskCompletion(id);
  };

  const handleCreateNew = () => {
    setEditingTask(undefined);
    setIsModalOpen(true);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setEditingTask(undefined);
  };

  const filterProps = {
    filter,
    onFilterChange: setFilter,
    priorityFilter,
    onPriorityFilterChange: setPriorityFilter,
  };

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <TaskFilter {...filterProps} />
          <Button onClick={handleCreateNew} size="sm">
            <Plus className="h-4 w-4" />
            New Task
          </Button>
        </div>
        <div className="rounded-xl border border-red-500/20 bg-red-950/20 p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
            <div className="space-y-2">
              <p className="text-sm text-red-300">
                Error loading tasks: {error.message || 'An unknown error occurred'}
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={loadTasks}
                className="border-red-500/30 text-red-300 hover:bg-red-950/40"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Retry
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <TaskFilter {...filterProps} />
        </div>
        <div className="space-y-3">
          {[...Array(3)].map((_, index) => (
            <div key={index} className="rounded-xl border border-zinc-800/60 bg-zinc-900/30 p-5 animate-pulse">
              <div className="flex justify-between items-start mb-3">
                <div className="h-5 w-3/5 bg-zinc-800 rounded" />
                <div className="h-6 w-16 bg-zinc-800 rounded-full" />
              </div>
              <div className="h-4 w-full bg-zinc-800/60 rounded mb-2" />
              <div className="h-4 w-2/3 bg-zinc-800/60 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <TaskFilter {...filterProps} />
        <Button onClick={handleCreateNew} size="sm">
          <Plus className="h-4 w-4" />
          New Task
        </Button>
      </div>

      {filteredTasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 px-4">
          <div className="h-14 w-14 rounded-2xl bg-zinc-800/60 flex items-center justify-center mb-4">
            <Inbox className="h-7 w-7 text-zinc-600" />
          </div>
          <h3 className="text-lg font-semibold text-zinc-300 mb-1">
            {filter === 'all' && priorityFilter === 'all' ? 'No tasks yet' : 'No matching tasks'}
          </h3>
          <p className="text-sm text-zinc-500 text-center max-w-xs mb-5">
            {filter === 'all' && priorityFilter === 'all'
              ? 'Get started by creating your first task'
              : 'No tasks match the current filters'}
          </p>
          {filter === 'all' && priorityFilter === 'all' && (
            <Button onClick={handleCreateNew} size="sm" variant="secondary">
              <Plus className="h-4 w-4" />
              Create your first task
            </Button>
          )}
        </div>
      ) : (
        <AnimatePresence mode="popLayout">
          <div className="space-y-3">
            {filteredTasks.map(task => (
              <TaskCard
                key={task.id}
                task={task}
                onEdit={handleEdit}
                onDelete={handleDelete}
                onToggleComplete={handleToggleComplete}
              />
            ))}
          </div>
        </AnimatePresence>
      )}

      <TaskModal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        task={editingTask}
        onCreateTask={createTask}
        onUpdateTask={updateTask}
      />
    </div>
  );
};

export default TaskList;
