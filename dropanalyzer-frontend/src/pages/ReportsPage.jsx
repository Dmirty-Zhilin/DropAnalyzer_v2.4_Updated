
import React, { useEffect, useState } from 'react';
import { getReports } from '../lib/api-client';

function ReportsPage() {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filter, setFilter] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        const fetchReports = async () => {
            try {
                const response = await getReports();
                setReports(response.data || []);
            } catch (err) {
                setError(err);
            } finally {
                setLoading(false);
            }
        };
        fetchReports();
    }, []);

    const getQualityColor = (category) => {
        switch (category) {
            case 'Recommended':
                return 'bg-green-100 text-green-800';
            case 'Low Quality':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const filteredReports = reports.filter(report => {
        const matchesSearch = report.domain.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesFilter = filter === 'all' || 
            (filter === 'recommended' && report.recommended) ||
            (filter === 'low_quality' && !report.recommended);
        return matchesSearch && matchesFilter;
    });

    if (loading) return (
        <div className="flex items-center justify-center h-full">
            <div className="text-lg text-gray-600">Загрузка отчетов...</div>
        </div>
    );
    
    if (error) return (
        <div className="flex items-center justify-center h-full">
            <div className="text-red-600">Ошибка загрузки отчетов: {error.message}</div>
        </div>
    );

    return (
        <div className="p-6">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Reports</h1>
                <p className="text-gray-600 mt-2">Управление вашими отчетами анализа доменов</p>
            </div>

            {/* Filters */}
            <div className="mb-6 flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                    <input
                        type="text"
                        placeholder="Поиск доменов..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                </div>
                <div className="flex gap-2">
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                        <option value="all">Все домены</option>
                        <option value="recommended">Рекомендуемые</option>
                        <option value="low_quality">Низкое качество</option>
                    </select>
                    <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                        Экспорт
                    </button>
                </div>
            </div>

            {/* Reports Table */}
            <div className="bg-white shadow-sm rounded-xl border border-gray-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">
                        Ваши отчеты
                    </h3>
                    <p className="text-sm text-gray-500 mt-1">
                        Всего отчетов: {filteredReports.length}
                    </p>
                </div>

                {filteredReports.length === 0 ? (
                    <div className="text-center py-12">
                        <div className="text-gray-500 text-lg">Нет отчетов для отображения</div>
                        <div className="text-sm text-gray-400 mt-2">
                            {searchTerm || filter !== 'all' 
                                ? 'Попробуйте изменить фильтры поиска'
                                : 'Начните анализ доменов для создания отчетов'
                            }
                        </div>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Домен
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Качество
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Снимки
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Годы покрытия
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Последний снимок
                                    </th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Действия
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {filteredReports.map((report, index) => (
                                    <tr key={index} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-medium text-gray-900">
                                                {report.domain}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getQualityColor(report.category)}`}>
                                                {report.category}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {report.total_snapshots || 0}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                            {report.years_covered || 0}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {report.last_snapshot ? new Date(report.last_snapshot).toLocaleDateString('ru-RU') : 'Нет данных'}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <button className="text-blue-600 hover:text-blue-900 mr-3">
                                                Просмотр
                                            </button>
                                            <button className="text-red-600 hover:text-red-900">
                                                Удалить
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

export default ReportsPage;
