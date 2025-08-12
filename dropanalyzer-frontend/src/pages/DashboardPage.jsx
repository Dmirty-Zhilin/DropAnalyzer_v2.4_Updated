
import React, { useEffect, useState } from 'react';
import { getDashboardStats, getReports } from '../lib/api-client';

function DashboardPage() {
    const [dashboardData, setDashboardData] = useState(null);
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [dashboardResponse, reportsResponse] = await Promise.all([
                    getDashboardStats(),
                    getReports()
                ]);
                setDashboardData(dashboardResponse);
                setReports(reportsResponse.data || []);
            } catch (err) {
                setError(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const calculateStats = () => {
        if (!reports.length) {
            return {
                totalDomains: 0,
                domainsWithSnapshots: 0,
                goodDomains: 0,
                recommendedDomains: 0,
                recentlyActive: 0,
                qualityDistribution: {
                    recommended: 0,
                    lowQuality: 0,
                    excellent: 0,
                    veryGood: 0,
                    good: 0,
                    fair: 0,
                    poor: 0
                }
            };
        }

        const totalDomains = reports.length;
        const domainsWithSnapshots = reports.filter(r => r.has_snapshots).length;
        const goodDomains = reports.filter(r => r.is_good).length;
        const recommendedDomains = reports.filter(r => r.recommended).length;
        const recentlyActive = reports.filter(r => {
            if (!r.last_snapshot) return false;
            const lastSnapshot = new Date(r.last_snapshot);
            const currentYear = new Date().getFullYear();
            return lastSnapshot.getFullYear() === currentYear;
        }).length;

        const qualityDistribution = {
            recommended: reports.filter(r => r.recommended).length,
            lowQuality: reports.filter(r => !r.recommended).length,
            excellent: 0,
            veryGood: 0,
            good: 0,
            fair: 0,
            poor: 0
        };

        return {
            totalDomains,
            domainsWithSnapshots,
            goodDomains,
            recommendedDomains,
            recentlyActive,
            qualityDistribution
        };
    };

    if (loading) return (
        <div className="flex items-center justify-center h-full">
            <div className="text-lg text-gray-600">Загрузка дашборда...</div>
        </div>
    );
    
    if (error) return (
        <div className="flex items-center justify-center h-full">
            <div className="text-red-600">Ошибка загрузки дашборда: {error.message}</div>
        </div>
    );

    const stats = calculateStats();

    return (
        <div className="p-6">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                <p className="text-gray-600 mt-2">Обзор анализа доменов и статистика</p>
            </div>
            
            {/* Main Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
                <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-gray-200">
                    <div className="p-6">
                        <div className="flex items-center">
                            <div className="flex-shrink-0">
                                <div className="text-3xl">🌐</div>
                            </div>
                            <div className="ml-4 w-0 flex-1">
                                <dl>
                                    <dt className="text-sm font-medium text-gray-500 truncate">
                                        Всего доменов
                                    </dt>
                                    <dd className="text-2xl font-bold text-gray-900">
                                        {stats.totalDomains}
                                    </dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-gray-200">
                    <div className="p-6">
                        <div className="flex items-center">
                            <div className="flex-shrink-0">
                                <div className="text-3xl">📸</div>
                            </div>
                            <div className="ml-4 w-0 flex-1">
                                <dl>
                                    <dt className="text-sm font-medium text-gray-500 truncate">
                                        Со снимками
                                    </dt>
                                    <dd className="text-2xl font-bold text-gray-900">
                                        {stats.domainsWithSnapshots}
                                    </dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-gray-200">
                    <div className="p-6">
                        <div className="flex items-center">
                            <div className="flex-shrink-0">
                                <div className="text-3xl">✅</div>
                            </div>
                            <div className="ml-4 w-0 flex-1">
                                <dl>
                                    <dt className="text-sm font-medium text-gray-500 truncate">
                                        Хорошие домены
                                    </dt>
                                    <dd className="text-2xl font-bold text-gray-900">
                                        {stats.goodDomains}
                                    </dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-gray-200">
                    <div className="p-6">
                        <div className="flex items-center">
                            <div className="flex-shrink-0">
                                <div className="text-3xl">⭐</div>
                            </div>
                            <div className="ml-4 w-0 flex-1">
                                <dl>
                                    <dt className="text-sm font-medium text-gray-500 truncate">
                                        Рекомендуемые
                                    </dt>
                                    <dd className="text-2xl font-bold text-gray-900">
                                        {stats.recommendedDomains}
                                    </dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bg-white overflow-hidden shadow-sm rounded-xl border border-gray-200">
                    <div className="p-6">
                        <div className="flex items-center">
                            <div className="flex-shrink-0">
                                <div className="text-3xl">🔥</div>
                            </div>
                            <div className="ml-4 w-0 flex-1">
                                <dl>
                                    <dt className="text-sm font-medium text-gray-500 truncate">
                                        Недавно активные
                                    </dt>
                                    <dd className="text-2xl font-bold text-gray-900">
                                        {stats.recentlyActive}
                                    </dd>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Quality Distribution */}
            <div className="bg-white shadow-sm rounded-xl border border-gray-200 p-6 mb-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-6">Распределение качества</h3>
                <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg">
                        <span className="text-sm font-medium text-green-800">Рекомендуемые (Long-Live)</span>
                        <span className="text-sm font-bold text-green-900">{stats.qualityDistribution?.recommended || 0} доменов</span>
                    </div>
                    <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
                        <span className="text-sm font-medium text-red-800">Низкое качество</span>
                        <span className="text-sm font-bold text-red-900">{stats.qualityDistribution?.lowQuality || 0} доменов</span>
                    </div>
                </div>
            </div>

            {/* Recent Analysis */}
            <div className="bg-white shadow-sm rounded-xl border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-6">Недавний анализ</h3>
                {reports.length === 0 ? (
                    <div className="text-center py-12">
                        <div className="text-gray-500 text-lg">Нет данных для отображения</div>
                        <div className="text-sm text-gray-400 mt-2">Начните анализ доменов для просмотра результатов</div>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {reports.slice(0, 5).map((report, index) => (
                            <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                                <div>
                                    <h4 className="text-sm font-medium text-gray-900">{report.domain}</h4>
                                    <p className="text-sm text-gray-500">Оценка: {report.quality_score || 0}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-sm text-gray-900">{report.total_snapshots || 0} снимков</p>
                                    <p className="text-sm text-gray-500">{report.years_covered || 0} лет</p>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default DashboardPage;
