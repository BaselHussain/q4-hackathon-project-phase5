'use client';

import { useState, useEffect } from 'react';
import { useAuth } from './useAuth';
import { Task, TaskPriority, TaskRecurrence, taskApi } from '@/lib/api';
import { toast } from 'sonner';
import { useErrorHandling } from './useErrorHandling';

// TaskData for create/update — includes advanced fields
interface TaskData {
  title: string;
  description?: string | undefined;
  priority?: TaskPriority | undefined;
  dueDate?: string | null | undefined;
  tags?: string[] | null | undefined;
  recurrence?: TaskRecurrence | undefined;
}

interface ApiError {
  message: string;
  status?: number | undefined;
}

// Custom hook for managing tasks
export const useTasks = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<ApiError | null>(null);
  const { user } = useAuth();
  const { handleError } = useErrorHandling();

  // Load tasks from the API
  const loadTasks = async (): Promise<void> => {
    if (!user) {
      setError({ message: 'User not authenticated' });
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // taskApi.getTasks() returns Task[] directly (already transformed)
      const taskList = await taskApi.getTasks();
      const sortedTasks = taskList.sort(
        (a: Task, b: Task) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );

      setTasks(sortedTasks);
    } catch (err: any) {
      const apiError = handleError(err);
      setError({
        message: apiError.message,
        status: apiError.status,
      });
      console.error('Error loading tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  // Create a new task
  const createTask = async (taskData: TaskData): Promise<Task | null> => {
    if (!user) {
      setError({ message: 'User not authenticated' });
      return null;
    }

    try {
      setError(null);

      // Optimistic update
      const tempTask: Task = {
        id: `temp-${Date.now()}`,
        title: taskData.title,
        description: taskData.description,
        status: 'pending',
        priority: taskData.priority ?? 'medium',
        dueDate: taskData.dueDate ?? null,
        tags: taskData.tags ?? null,
        recurrence: taskData.recurrence ?? 'none',
        userId: user.id,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      setTasks(prev => [tempTask, ...prev]);

      const newTask = await taskApi.createTask({
        title: taskData.title,
        description: taskData.description,
        priority: taskData.priority,
        dueDate: taskData.dueDate,
        tags: taskData.tags,
        recurrence: taskData.recurrence,
      });

      // Replace temp task with real one
      setTasks(prev => [
        newTask,
        ...prev.filter(task => task.id !== tempTask.id)
      ]);

      toast.success('Task created successfully!');
      return newTask;
    } catch (err: any) {
      const apiError = handleError(err);
      setError({
        message: apiError.message,
        status: apiError.status,
      });

      // Remove temp task on failure
      setTasks(prev => prev.filter(task => !task.id.startsWith('temp-')));
      toast.error('Failed to create task');
      return null;
    }
  };

  // Update an existing task
  const updateTask = async (id: string, taskData: {
    title?: string | undefined;
    description?: string | undefined;
    priority?: TaskPriority | undefined;
    dueDate?: string | null | undefined;
    tags?: string[] | null | undefined;
    recurrence?: TaskRecurrence | undefined;
  }): Promise<Task | null> => {
    if (!user) {
      setError({ message: 'User not authenticated' });
      return null;
    }

    try {
      setError(null);

      // Optimistic update — only spread defined values to avoid overwriting with undefined
      const definedUpdates: Record<string, string> = {};
      if (taskData.title !== undefined) definedUpdates.title = taskData.title;
      if (taskData.description !== undefined) definedUpdates.description = taskData.description;

      setTasks(prev => prev.map(task =>
        task.id === id ? { ...task, ...definedUpdates, updatedAt: new Date().toISOString() } : task
      ));

      const updatedTask = await taskApi.updateTask(id, taskData);

      // Replace with server response
      setTasks(prev => prev.map(task => task.id === id ? updatedTask : task));

      toast.success('Task updated successfully!');
      return updatedTask;
    } catch (err: any) {
      const apiError = handleError(err);
      setError({
        message: apiError.message,
        status: apiError.status,
      });
      // Reload to restore correct state
      await loadTasks();
      toast.error('Failed to update task');
      return null;
    }
  };

  // Delete a task
  const deleteTask = async (id: string, showToast: boolean = true): Promise<boolean> => {
    if (!user) {
      setError({ message: 'User not authenticated' });
      return false;
    }

    const deletedTask = tasks.find(task => task.id === id);

    try {
      setError(null);

      // Optimistic removal
      setTasks(prev => prev.filter(task => task.id !== id));

      if (showToast && deletedTask) {
        toast.info(`Task "${deletedTask.title}" deleted`, {
          action: {
            label: 'Undo',
            onClick: () => {
              // Restore and recreate
              setTasks(prev => [...prev, deletedTask]);
              taskApi.createTask({
                title: deletedTask.title,
                description: deletedTask.description,
              }).catch(() => {
                toast.error('Failed to restore task');
                setTasks(prev => prev.filter(t => t.id !== deletedTask.id));
              });
            },
          },
          duration: 5000,
        });
      }

      await taskApi.deleteTask(id);
      return true;
    } catch (err: any) {
      const apiError = handleError(err);
      setError({
        message: apiError.message,
        status: apiError.status,
      });

      // Restore on failure
      if (deletedTask) {
        setTasks(prev => [...prev, deletedTask]);
      }
      return false;
    }
  };

  // Toggle task completion — uses PATCH .../complete endpoint
  const toggleTaskCompletion = async (id: string): Promise<Task | null> => {
    const task = tasks.find(t => t.id === id);
    if (!task) return null;

    try {
      // Optimistic toggle
      const newStatus = task.status === 'completed' ? 'pending' : 'completed';
      setTasks(prev => prev.map(t =>
        t.id === id ? { ...t, status: newStatus as Task['status'] } : t
      ));

      const updatedTask = await taskApi.toggleComplete(id);

      // Replace with server response
      setTasks(prev => prev.map(t => t.id === id ? updatedTask : t));

      toast.success(updatedTask.status === 'completed' ? 'Task completed!' : 'Task marked as pending');
      return updatedTask;
    } catch (err: any) {
      // Revert optimistic update
      setTasks(prev => prev.map(t =>
        t.id === id ? { ...t, status: task.status } : t
      ));
      toast.error('Failed to update task status');
      return null;
    }
  };

  // Refresh tasks when mounted or user changes
  useEffect(() => {
    if (user) {
      loadTasks();
    } else {
      setTasks([]);
      setLoading(false);
    }
  }, [user]);

  return {
    tasks,
    loading,
    error,
    loadTasks,
    createTask,
    updateTask,
    deleteTask,
    toggleTaskCompletion,
  };
};
