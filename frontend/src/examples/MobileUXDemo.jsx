/**
 * MobileUXDemo - Demonstration of advanced mobile UX features
 *
 * This file demonstrates:
 * - SwipeableRow with swipe-to-action
 * - PullToRefresh with gesture detection
 * - Integration with existing components
 * - Best practices for mobile UX
 */

import { useState } from 'react';
import { Trash2, Edit, Archive, Star, Mail, Check, X } from 'lucide-react';
import {
  SwipeableRow,
  SwipeableRowProvider,
} from '../components/ui/SwipeableRow.jsx';
import PullToRefresh from '../components/ui/PullToRefresh.jsx';
import { usePullToRefresh, PULL_STATES } from '../hooks/usePullToRefresh.js';

// ============================================================================
// Example 1: Basic SwipeableRow usage
// ============================================================================

export function BasicSwipeableRowExample() {
  const [items, setItems] = useState([
    { id: 1, title: 'Facture #1234', status: 'pending', amount: '250.00€' },
    { id: 2, title: 'Facture #1235', status: 'pending', amount: '180.50€' },
    { id: 3, title: 'Facture #1236', status: 'pending', amount: '420.00€' },
  ]);

  const handleDelete = (item) => {
    setItems(prev => prev.filter(i => i.id !== item.id));
  };

  const handleEdit = (item) => {
    console.log('Edit item:', item);
  };

  const handleArchive = (item) => {
    console.log('Archive item:', item);
  };

  return (
    <SwipeableRowProvider>
      <div className="space-y-3">
        <h3 className="text-lg font-semibold mb-4">Swipeable Invoices</h3>
        {items.map((item) => (
          <SwipeableRow
            key={item.id}
            id={`invoice-${item.id}`}
            leftActions={[
              {
                label: 'Supprimer',
                icon: Trash2,
                variant: 'danger',
                onAction: () => handleDelete(item),
              },
            ]}
            rightActions={[
              {
                label: 'Éditer',
                icon: Edit,
                variant: 'primary',
                onAction: () => handleEdit(item),
              },
              {
                label: 'Archiver',
                icon: Archive,
                variant: 'success',
                onAction: () => handleArchive(item),
              },
            ]}
          >
            <div className="bg-white rounded-lg border border-slate-200 p-4">
              <div className="flex justify-between items-start">
                <div>
                  <div className="font-semibold text-slate-900">{item.title}</div>
                  <div className="text-sm text-slate-500 mt-1">
                    Status: <span className="font-medium">{item.status}</span>
                  </div>
                </div>
                <div className="text-lg font-bold text-slate-900">{item.amount}</div>
              </div>
            </div>
          </SwipeableRow>
        ))}
      </div>
    </SwipeableRowProvider>
  );
}

// ============================================================================
// Example 2: Email-style swipeable list with quick actions
// ============================================================================

export function EmailListExample() {
  const [emails, setEmails] = useState([
    {
      id: 1,
      sender: 'John Doe',
      subject: 'Meeting Tomorrow',
      preview: 'Hey, just wanted to confirm...',
      time: '10:30',
      unread: true,
      starred: false,
    },
    {
      id: 2,
      sender: 'Jane Smith',
      subject: 'Project Update',
      preview: 'The latest changes have been...',
      time: '09:15',
      unread: true,
      starred: true,
    },
    {
      id: 3,
      sender: 'Team',
      subject: 'Weekly Report',
      preview: 'Here is the summary of this week...',
      time: 'Yesterday',
      unread: false,
      starred: false,
    },
  ]);

  const handleArchive = (email) => {
    setEmails(prev => prev.filter(e => e.id !== email.id));
  };

  const handleMarkRead = (email) => {
    setEmails(prev =>
      prev.map(e =>
        e.id === email.id ? { ...e, unread: !e.unread } : e
      )
    );
  };

  const handleToggleStar = (email) => {
    setEmails(prev =>
      prev.map(e =>
        e.id === email.id ? { ...e, starred: !e.starred } : e
      )
    );
  };

  return (
    <SwipeableRowProvider>
      <div className="space-y-2">
        <h3 className="text-lg font-semibold mb-4">Inbox</h3>
        {emails.map((email) => (
          <SwipeableRow
            key={email.id}
            id={`email-${email.id}`}
            leftActions={[
              {
                label: 'Archive',
                icon: Archive,
                variant: 'danger',
                onAction: () => handleArchive(email),
              },
            ]}
            rightActions={[
              {
                label: email.unread ? 'Mark Read' : 'Mark Unread',
                icon: email.unread ? Check : Mail,
                variant: 'primary',
                onAction: () => handleMarkRead(email),
              },
            ]}
            longPressActions={[
              {
                label: email.starred ? 'Unstar' : 'Star',
                icon: Star,
                onAction: () => handleToggleStar(email),
              },
              {
                label: 'Archive',
                icon: Archive,
                variant: 'danger',
                onAction: () => handleArchive(email),
              },
            ]}
          >
            <div
              className={`bg-white rounded-lg border p-4 ${
                email.unread ? 'border-brand-500 bg-brand-50/50' : 'border-slate-200'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`font-semibold truncate ${
                        email.unread ? 'text-slate-900' : 'text-slate-600'
                      }`}
                    >
                      {email.sender}
                    </span>
                    {email.starred && (
                      <Star className="h-4 w-4 fill-amber-400 text-amber-400 flex-shrink-0" />
                    )}
                  </div>
                  <div
                    className={`text-sm mb-1 truncate ${
                      email.unread ? 'font-semibold text-slate-900' : 'text-slate-600'
                    }`}
                  >
                    {email.subject}
                  </div>
                  <div className="text-sm text-slate-500 truncate">{email.preview}</div>
                </div>
                <div className="text-xs text-slate-500 flex-shrink-0">{email.time}</div>
              </div>
            </div>
          </SwipeableRow>
        ))}
      </div>
    </SwipeableRowProvider>
  );
}

// ============================================================================
// Example 3: PullToRefresh basic usage
// ============================================================================

export function BasicPullToRefreshExample() {
  const [items, setItems] = useState([
    { id: 1, name: 'Item 1' },
    { id: 2, name: 'Item 2' },
    { id: 3, name: 'Item 3' },
  ]);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  const handleRefresh = async () => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Update data
    setItems([
      { id: Date.now(), name: 'New Item' },
      ...items,
    ]);
    setLastRefresh(new Date());
  };

  return (
    <div className="max-w-md mx-auto">
      <h3 className="text-lg font-semibold mb-2">Pull to Refresh</h3>
      <p className="text-sm text-slate-600 mb-4">
        Last refresh: {lastRefresh.toLocaleTimeString()}
      </p>

      <PullToRefresh
        onRefresh={handleRefresh}
        className="h-96 bg-slate-50 rounded-lg border border-slate-200"
      >
        <div className="p-4 space-y-3">
          {items.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm"
            >
              <div className="font-medium text-slate-900">{item.name}</div>
            </div>
          ))}
        </div>
      </PullToRefresh>
    </div>
  );
}

// ============================================================================
// Example 4: Custom PullToRefresh indicator
// ============================================================================

export function CustomPullToRefreshExample() {
  const [data, setData] = useState([
    { id: 1, title: 'Transaction 1', amount: 100 },
    { id: 2, title: 'Transaction 2', amount: 200 },
    { id: 3, title: 'Transaction 3', amount: 150 },
  ]);

  const handleRefresh = async () => {
    await new Promise(resolve => setTimeout(resolve, 1500));
    setData([
      { id: Date.now(), title: 'New Transaction', amount: Math.random() * 500 },
      ...data,
    ]);
  };

  const customIndicator = (state, progress) => (
    <div className="flex items-center gap-2">
      <div
        className="h-8 w-8 rounded-full border-3 border-brand-500 border-t-transparent"
        style={{
          transform: `rotate(${progress * 360}deg)`,
          opacity: progress,
        }}
      />
      <span className="text-sm font-medium text-slate-600">
        {state === PULL_STATES.PULLING && `${Math.round(progress * 100)}%`}
        {state === PULL_STATES.READY && 'Relâchez !'}
        {state === PULL_STATES.REFRESHING && 'Chargement...'}
      </span>
    </div>
  );

  return (
    <div className="max-w-md mx-auto">
      <h3 className="text-lg font-semibold mb-4">Custom Indicator</h3>

      <PullToRefresh
        onRefresh={handleRefresh}
        renderIndicator={customIndicator}
        className="h-96 bg-slate-50 rounded-lg border border-slate-200"
      >
        <div className="p-4 space-y-3">
          {data.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-lg border border-slate-200 p-4"
            >
              <div className="flex justify-between items-center">
                <span className="font-medium text-slate-900">{item.title}</span>
                <span className="text-lg font-bold text-brand-500">
                  {item.amount.toFixed(2)}€
                </span>
              </div>
            </div>
          ))}
        </div>
      </PullToRefresh>
    </div>
  );
}

// ============================================================================
// Example 5: Combined - Swipeable list with PullToRefresh
// ============================================================================

export function CombinedExample() {
  const [tasks, setTasks] = useState([
    { id: 1, title: 'Review invoice #1234', completed: false, priority: 'high' },
    { id: 2, title: 'Update inventory', completed: false, priority: 'medium' },
    { id: 3, title: 'Call supplier', completed: true, priority: 'low' },
  ]);

  const handleRefresh = async () => {
    await new Promise(resolve => setTimeout(resolve, 1500));
    setTasks([
      {
        id: Date.now(),
        title: 'New task added',
        completed: false,
        priority: 'high',
      },
      ...tasks,
    ]);
  };

  const handleToggleComplete = (task) => {
    setTasks(prev =>
      prev.map(t =>
        t.id === task.id ? { ...t, completed: !t.completed } : t
      )
    );
  };

  const handleDelete = (task) => {
    setTasks(prev => prev.filter(t => t.id !== task.id));
  };

  const priorityColors = {
    high: 'text-rose-500 bg-rose-50',
    medium: 'text-amber-500 bg-amber-50',
    low: 'text-slate-500 bg-slate-50',
  };

  return (
    <div className="max-w-md mx-auto">
      <h3 className="text-lg font-semibold mb-4">Task List (Combined Demo)</h3>

      <PullToRefresh
        onRefresh={handleRefresh}
        className="h-96 bg-slate-50 rounded-lg border border-slate-200"
      >
        <SwipeableRowProvider>
          <div className="p-4 space-y-3">
            {tasks.map((task) => (
              <SwipeableRow
                key={task.id}
                id={`task-${task.id}`}
                leftActions={[
                  {
                    label: 'Delete',
                    icon: Trash2,
                    variant: 'danger',
                    onAction: () => handleDelete(task),
                  },
                ]}
                rightActions={[
                  {
                    label: task.completed ? 'Undo' : 'Complete',
                    icon: task.completed ? X : Check,
                    variant: 'success',
                    onAction: () => handleToggleComplete(task),
                  },
                ]}
              >
                <div className="bg-white rounded-lg border border-slate-200 p-4">
                  <div className="flex items-start gap-3">
                    <input
                      type="checkbox"
                      checked={task.completed}
                      onChange={() => handleToggleComplete(task)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div
                        className={`font-medium ${
                          task.completed
                            ? 'line-through text-slate-400'
                            : 'text-slate-900'
                        }`}
                      >
                        {task.title}
                      </div>
                      <div
                        className={`inline-block mt-2 px-2 py-1 rounded text-xs font-medium ${
                          priorityColors[task.priority]
                        }`}
                      >
                        {task.priority}
                      </div>
                    </div>
                  </div>
                </div>
              </SwipeableRow>
            ))}
          </div>
        </SwipeableRowProvider>
      </PullToRefresh>
    </div>
  );
}

// ============================================================================
// Example 6: Using the hook directly for custom implementation
// ============================================================================

export function CustomHookExample() {
  const [count, setCount] = useState(0);

  const {
    pullState,
    pullProgress,
    pullDistance,
    handlers,
    containerRef,
  } = usePullToRefresh({
    onRefresh: async () => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setCount(prev => prev + 1);
    },
    threshold: 80,
  });

  return (
    <div className="max-w-md mx-auto">
      <h3 className="text-lg font-semibold mb-4">Custom Hook Usage</h3>

      <div
        ref={containerRef}
        {...handlers}
        className="h-64 bg-slate-50 rounded-lg border border-slate-200 overflow-auto"
      >
        {/* Custom pull indicator */}
        {pullDistance > 0 && (
          <div
            className="bg-brand-50 border-b border-brand-200"
            style={{ height: pullDistance }}
          >
            <div className="h-full flex items-center justify-center">
              <div className="text-sm font-medium text-brand-600">
                Progress: {Math.round(pullProgress * 100)}%
              </div>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="p-6 text-center">
          <div className="text-4xl font-bold text-slate-900 mb-2">{count}</div>
          <div className="text-sm text-slate-600">
            Pull down to refresh and increment
          </div>
          <div className="mt-4 text-xs text-slate-400">
            State: {pullState}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Main Demo Component
// ============================================================================

export default function MobileUXDemo() {
  const [activeDemo, setActiveDemo] = useState('basic-swipe');

  const demos = [
    { id: 'basic-swipe', label: 'Basic Swipeable Row', component: BasicSwipeableRowExample },
    { id: 'email-list', label: 'Email List', component: EmailListExample },
    { id: 'basic-pull', label: 'Basic Pull to Refresh', component: BasicPullToRefreshExample },
    { id: 'custom-pull', label: 'Custom Indicator', component: CustomPullToRefreshExample },
    { id: 'combined', label: 'Combined Demo', component: CombinedExample },
    { id: 'custom-hook', label: 'Custom Hook', component: CustomHookExample },
  ];

  const ActiveComponent = demos.find(d => d.id === activeDemo)?.component || BasicSwipeableRowExample;

  return (
    <div className="min-h-screen bg-slate-100 p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Mobile UX Features Demo</h1>
        <p className="text-slate-600 mb-6">
          Advanced mobile gestures: swipe-to-action and pull-to-refresh
        </p>

        {/* Demo selector */}
        <div className="mb-6 flex flex-wrap gap-2">
          {demos.map((demo) => (
            <button
              key={demo.id}
              onClick={() => setActiveDemo(demo.id)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeDemo === demo.id
                  ? 'bg-brand-500 text-white'
                  : 'bg-white text-slate-700 hover:bg-slate-50 border border-slate-200'
              }`}
            >
              {demo.label}
            </button>
          ))}
        </div>

        {/* Active demo */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <ActiveComponent />
        </div>

        {/* Instructions */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">How to use:</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Swipe left on rows to reveal delete action</li>
            <li>• Swipe right on rows to reveal edit/complete actions</li>
            <li>• Swipe quickly or past threshold to auto-execute action</li>
            <li>• Long press on rows for context menu</li>
            <li>• Pull down from the top to refresh content</li>
            <li>• Opening a row auto-closes other open rows</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
