import { useMemo } from 'react';

const CATEGORY_COLORS = {
  web: 'bg-blue-500',
  pwn: 'bg-red-500',
  crypto: 'bg-yellow-500',
  forensics: 'bg-green-500',
  reverse: 'bg-orange-500',
  misc: 'bg-neutral-500',
  osint: 'bg-cyan-500',
  steganography: 'bg-purple-500',
};

const CtfOverview = ({ cards }) => {
  const challenges = useMemo(() =>
    cards.filter(c => c.card_type === 'challenge'),
    [cards]
  );

  const stats = useMemo(() => {
    const captured = challenges.filter(c => c.flag_status === 'captured');
    const inProgress = challenges.filter(c => c.flag_status === 'in_progress');
    const totalPoints = challenges.reduce((sum, c) => sum + (c.points || 0), 0);
    const capturedPoints = captured.reduce((sum, c) => sum + (c.points || 0), 0);

    // Category breakdown
    const categories = {};
    challenges.forEach(c => {
      const cat = c.challenge_category || 'misc';
      if (!categories[cat]) {
        categories[cat] = { total: 0, captured: 0, totalPoints: 0, capturedPoints: 0 };
      }
      categories[cat].total++;
      categories[cat].totalPoints += c.points || 0;
      if (c.flag_status === 'captured') {
        categories[cat].captured++;
        categories[cat].capturedPoints += c.points || 0;
      }
    });

    return {
      total: challenges.length,
      captured: captured.length,
      inProgress: inProgress.length,
      totalPoints,
      capturedPoints,
      completion: challenges.length > 0 ? Math.round((captured.length / challenges.length) * 100) : 0,
      categories,
      recentSolves: captured
        .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
        .slice(0, 5),
    };
  }, [challenges]);

  if (challenges.length === 0) {
    return (
      <div className="text-center py-8 text-neutral-500 dark:text-neutral-400">
        <span className="text-4xl mb-3 block">&#9873;</span>
        <p className="text-sm">No challenges yet. Create a "Challenge" card to get started.</p>
      </div>
    );
  }

  // Sort challenges: in_progress first, then not_captured, then captured
  const statusOrder = { in_progress: 0, not_captured: 1, captured: 2 };
  const sortedChallenges = [...challenges].sort((a, b) => {
    const aOrder = statusOrder[a.flag_status] ?? 1;
    const bOrder = statusOrder[b.flag_status] ?? 1;
    if (aOrder !== bOrder) return aOrder - bOrder;
    return (b.points || 0) - (a.points || 0);
  });

  return (
    <div className="space-y-6">
      {/* Score Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{stats.capturedPoints}</p>
          <p className="text-xs text-neutral-500 dark:text-neutral-400">/ {stats.totalPoints} pts</p>
          <p className="text-xs font-medium text-neutral-600 dark:text-neutral-300 mt-1">Score</p>
        </div>
        <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.captured}</p>
          <p className="text-xs text-neutral-500 dark:text-neutral-400">/ {stats.total} challenges</p>
          <p className="text-xs font-medium text-neutral-600 dark:text-neutral-300 mt-1">Solved</p>
        </div>
        <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{stats.inProgress}</p>
          <p className="text-xs text-neutral-500 dark:text-neutral-400">working on</p>
          <p className="text-xs font-medium text-neutral-600 dark:text-neutral-300 mt-1">In Progress</p>
        </div>
        <div className="bg-white dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-neutral-800 dark:text-neutral-200">{stats.completion}%</p>
          <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-1.5 mt-2">
            <div
              className="bg-purple-600 h-1.5 rounded-full transition-all"
              style={{ width: `${stats.completion}%` }}
            />
          </div>
          <p className="text-xs font-medium text-neutral-600 dark:text-neutral-300 mt-1">Completion</p>
        </div>
      </div>

      {/* Category Breakdown */}
      {Object.keys(stats.categories).length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-3">Category Breakdown</h3>
          <div className="space-y-2">
            {Object.entries(stats.categories)
              .sort((a, b) => b[1].totalPoints - a[1].totalPoints)
              .map(([cat, data]) => {
                const pct = data.total > 0 ? Math.round((data.captured / data.total) * 100) : 0;
                return (
                  <div key={cat} className="flex items-center gap-3">
                    <span className="text-xs font-medium text-neutral-600 dark:text-neutral-300 w-24 capitalize">{cat}</span>
                    <div className="flex-1 bg-neutral-200 dark:bg-neutral-700 rounded-full h-2">
                      <div
                        className={`${CATEGORY_COLORS[cat] || 'bg-neutral-500'} h-2 rounded-full transition-all`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-xs text-neutral-500 dark:text-neutral-400 w-20 text-right">
                      {data.captured}/{data.total} ({data.capturedPoints}/{data.totalPoints} pts)
                    </span>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Challenge List */}
      <div>
        <h3 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-3">Challenges</h3>
        <div className="space-y-1">
          {sortedChallenges.map(challenge => (
            <div
              key={challenge.id}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg border text-sm ${
                challenge.flag_status === 'captured'
                  ? 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800 opacity-70'
                  : challenge.flag_status === 'in_progress'
                  ? 'bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-800'
                  : 'bg-white dark:bg-neutral-800 border-neutral-200 dark:border-neutral-700'
              }`}
            >
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                challenge.flag_status === 'captured' ? 'bg-green-500' :
                challenge.flag_status === 'in_progress' ? 'bg-yellow-500' : 'bg-neutral-400'
              }`} />
              <span className={`px-1.5 py-0.5 text-xs rounded capitalize ${CATEGORY_COLORS[challenge.challenge_category] ? 'text-white ' + CATEGORY_COLORS[challenge.challenge_category] : 'bg-neutral-200 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-400'}`}>
                {challenge.challenge_category || 'misc'}
              </span>
              <span className="font-medium text-neutral-900 dark:text-neutral-100 flex-1 truncate">
                {challenge.title}
              </span>
              <span className="text-xs font-mono text-purple-600 dark:text-purple-400 flex-shrink-0">
                {challenge.points ?? 0} pts
              </span>
              <span className={`text-xs font-medium capitalize flex-shrink-0 ${
                challenge.flag_status === 'captured' ? 'text-green-600 dark:text-green-400' :
                challenge.flag_status === 'in_progress' ? 'text-yellow-600 dark:text-yellow-400' :
                'text-neutral-500 dark:text-neutral-400'
              }`}>
                {(challenge.flag_status || 'not_captured').replace('_', ' ')}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Solves */}
      {stats.recentSolves.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-neutral-700 dark:text-neutral-300 mb-3">Recent Solves</h3>
          <div className="space-y-1">
            {stats.recentSolves.map(solve => (
              <div key={solve.id} className="flex items-center gap-3 px-3 py-2 text-sm">
                <span className="text-green-500">&#10003;</span>
                <span className="font-medium text-neutral-900 dark:text-neutral-100">{solve.title}</span>
                <span className="text-xs text-purple-600 dark:text-purple-400 font-mono">+{solve.points ?? 0} pts</span>
                <span className="text-xs text-neutral-500 dark:text-neutral-400 ml-auto">
                  {new Date(solve.updated_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CtfOverview;
