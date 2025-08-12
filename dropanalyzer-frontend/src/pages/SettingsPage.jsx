
import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Bot, 
  Key, 
  Globe, 
  Database,
  Save,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Eye,
  EyeOff
} from 'lucide-react';

function SettingsPage() {
  const [activeTab, setActiveTab] = useState('llm');
  const [showApiKey, setShowApiKey] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);
  
  const [llmSettings, setLlmSettings] = useState({
    provider: 'openrouter',
    apiKey: 'sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
    model: 'anthropic/claude-3.5-sonnet',
    temperature: 0.7,
    maxTokens: 4000,
    systemPrompt: `Вы - эксперт по анализу доменов. Ваша задача - анализировать домены и предоставлять детальную информацию об их качестве, истории и потенциале.

При анализе домена учитывайте:
1. Историю снимков в Wayback Machine
2. Количество и качество снимков
3. Периоды активности и неактивности
4. Тематику и содержание сайта
5. Техническую информацию (SSL, DNS записи)

Предоставляйте структурированный анализ с рекомендациями по использованию домена.`
  });

  const [systemSettings, setSystemSettings] = useState({
    analysisTimeout: 30,
    maxConcurrentAnalysis: 5,
    cacheExpiration: 24,
    enableLogging: true,
    logLevel: 'INFO',
    autoBackup: true,
    backupInterval: 7
  });

  const [apiSettings, setApiSettings] = useState({
    waybackMachineTimeout: 15,
    cdxApiTimeout: 10,
    retryAttempts: 3,
    retryDelay: 2,
    rateLimitDelay: 1
  });

  const tabs = [
    { id: 'llm', label: 'LLM настройки', icon: Bot },
    { id: 'system', label: 'Система', icon: Settings },
    { id: 'api', label: 'API конфигурация', icon: Globe }
  ];

  const llmProviders = [
    { value: 'openrouter', label: 'OpenRouter' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'anthropic', label: 'Anthropic' },
    { value: 'local', label: 'Local Model' }
  ];

  const availableModels = {
    openrouter: [
      'anthropic/claude-3.5-sonnet',
      'anthropic/claude-3-haiku',
      'openai/gpt-4o',
      'openai/gpt-4o-mini',
      'meta-llama/llama-3.1-405b-instruct',
      'google/gemini-pro-1.5'
    ],
    openai: [
      'gpt-4o',
      'gpt-4o-mini',
      'gpt-4-turbo',
      'gpt-3.5-turbo'
    ],
    anthropic: [
      'claude-3-5-sonnet-20241022',
      'claude-3-haiku-20240307',
      'claude-3-opus-20240229'
    ],
    local: [
      'llama-3.1-8b',
      'llama-3.1-70b',
      'mistral-7b',
      'codellama-13b'
    ]
  };

  const handleSave = async (settingsType) => {
    setSaveStatus('saving');
    
    // Имитация API вызова
    setTimeout(() => {
      setSaveStatus('success');
      setTimeout(() => setSaveStatus(null), 3000);
    }, 1000);
  };

  const handleTestConnection = async () => {
    setSaveStatus('testing');
    
    // Имитация тестирования подключения
    setTimeout(() => {
      setSaveStatus('test-success');
      setTimeout(() => setSaveStatus(null), 3000);
    }, 2000);
  };

  const renderLLMSettings = () => (
    <div className="space-y-6">
      <div className="bg-white shadow-sm rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Bot className="h-5 w-5 mr-2" />
          Конфигурация LLM
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Провайдер
            </label>
            <select
              value={llmSettings.provider}
              onChange={(e) => setLlmSettings({ ...llmSettings, provider: e.target.value, model: availableModels[e.target.value][0] })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {llmProviders.map(provider => (
                <option key={provider.value} value={provider.value}>
                  {provider.label}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Модель
            </label>
            <select
              value={llmSettings.model}
              onChange={(e) => setLlmSettings({ ...llmSettings, model: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {availableModels[llmSettings.provider]?.map(model => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </div>
          
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API ключ
            </label>
            <div className="relative">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={llmSettings.apiKey}
                onChange={(e) => setLlmSettings({ ...llmSettings, apiKey: e.target.value })}
                className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showApiKey ? (
                  <EyeOff className="h-5 w-5 text-gray-400" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400" />
                )}
              </button>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Temperature ({llmSettings.temperature})
            </label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={llmSettings.temperature}
              onChange={(e) => setLlmSettings({ ...llmSettings, temperature: parseFloat(e.target.value) })}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Консервативно</span>
              <span>Креативно</span>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Максимум токенов
            </label>
            <input
              type="number"
              value={llmSettings.maxTokens}
              onChange={(e) => setLlmSettings({ ...llmSettings, maxTokens: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
        
        <div className="mt-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Системный промпт
          </label>
          <textarea
            value={llmSettings.systemPrompt}
            onChange={(e) => setLlmSettings({ ...llmSettings, systemPrompt: e.target.value })}
            rows={8}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        
        <div className="flex justify-between mt-6">
          <button
            onClick={handleTestConnection}
            className="flex items-center px-4 py-2 text-blue-600 border border-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Тест подключения
          </button>
          
          <button
            onClick={() => handleSave('llm')}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Save className="h-4 w-4 mr-2" />
            Сохранить
          </button>
        </div>
      </div>
    </div>
  );

  const renderSystemSettings = () => (
    <div className="space-y-6">
      <div className="bg-white shadow-sm rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Settings className="h-5 w-5 mr-2" />
          Системные настройки
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Таймаут анализа (секунды)
            </label>
            <input
              type="number"
              value={systemSettings.analysisTimeout}
              onChange={(e) => setSystemSettings({ ...systemSettings, analysisTimeout: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Максимум одновременных анализов
            </label>
            <input
              type="number"
              value={systemSettings.maxConcurrentAnalysis}
              onChange={(e) => setSystemSettings({ ...systemSettings, maxConcurrentAnalysis: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Срок действия кэша (часы)
            </label>
            <input
              type="number"
              value={systemSettings.cacheExpiration}
              onChange={(e) => setSystemSettings({ ...systemSettings, cacheExpiration: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Уровень логирования
            </label>
            <select
              value={systemSettings.logLevel}
              onChange={(e) => setSystemSettings({ ...systemSettings, logLevel: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="DEBUG">DEBUG</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Интервал резервного копирования (дни)
            </label>
            <input
              type="number"
              value={systemSettings.backupInterval}
              onChange={(e) => setSystemSettings({ ...systemSettings, backupInterval: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
        
        <div className="mt-6 space-y-4">
          <div className="flex items-center">
            <input
              type="checkbox"
              id="enableLogging"
              checked={systemSettings.enableLogging}
              onChange={(e) => setSystemSettings({ ...systemSettings, enableLogging: e.target.checked })}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="enableLogging" className="ml-2 block text-sm text-gray-900">
              Включить логирование
            </label>
          </div>
          
          <div className="flex items-center">
            <input
              type="checkbox"
              id="autoBackup"
              checked={systemSettings.autoBackup}
              onChange={(e) => setSystemSettings({ ...systemSettings, autoBackup: e.target.checked })}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="autoBackup" className="ml-2 block text-sm text-gray-900">
              Автоматическое резервное копирование
            </label>
          </div>
        </div>
        
        <div className="flex justify-end mt-6">
          <button
            onClick={() => handleSave('system')}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Save className="h-4 w-4 mr-2" />
            Сохранить
          </button>
        </div>
      </div>
    </div>
  );

  const renderApiSettings = () => (
    <div className="space-y-6">
      <div className="bg-white shadow-sm rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Globe className="h-5 w-5 mr-2" />
          API конфигурация
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Таймаут Wayback Machine (сек)
            </label>
            <input
              type="number"
              value={apiSettings.waybackMachineTimeout}
              onChange={(e) => setApiSettings({ ...apiSettings, waybackMachineTimeout: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Таймаут CDX API (сек)
            </label>
            <input
              type="number"
              value={apiSettings.cdxApiTimeout}
              onChange={(e) => setApiSettings({ ...apiSettings, cdxApiTimeout: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Количество повторных попыток
            </label>
            <input
              type="number"
              value={apiSettings.retryAttempts}
              onChange={(e) => setApiSettings({ ...apiSettings, retryAttempts: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Задержка между попытками (сек)
            </label>
            <input
              type="number"
              value={apiSettings.retryDelay}
              onChange={(e) => setApiSettings({ ...apiSettings, retryDelay: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Задержка rate limit (сек)
            </label>
            <input
              type="number"
              step="0.1"
              value={apiSettings.rateLimitDelay}
              onChange={(e) => setApiSettings({ ...apiSettings, rateLimitDelay: parseFloat(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
        
        <div className="flex justify-end mt-6">
          <button
            onClick={() => handleSave('api')}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Save className="h-4 w-4 mr-2" />
            Сохранить
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-2">Конфигурация системы и интеграций</p>
      </div>

      {/* Status Messages */}
      {saveStatus && (
        <div className={`mb-6 p-4 rounded-lg flex items-center ${
          saveStatus === 'success' || saveStatus === 'test-success' 
            ? 'bg-green-50 text-green-800' 
            : saveStatus === 'saving' || saveStatus === 'testing'
            ? 'bg-blue-50 text-blue-800'
            : 'bg-red-50 text-red-800'
        }`}>
          {saveStatus === 'success' && <CheckCircle className="h-5 w-5 mr-2" />}
          {saveStatus === 'test-success' && <CheckCircle className="h-5 w-5 mr-2" />}
          {(saveStatus === 'saving' || saveStatus === 'testing') && <RefreshCw className="h-5 w-5 mr-2 animate-spin" />}
          {saveStatus === 'error' && <AlertCircle className="h-5 w-5 mr-2" />}
          
          {saveStatus === 'success' && 'Настройки успешно сохранены'}
          {saveStatus === 'test-success' && 'Подключение успешно протестировано'}
          {saveStatus === 'saving' && 'Сохранение настроек...'}
          {saveStatus === 'testing' && 'Тестирование подключения...'}
          {saveStatus === 'error' && 'Ошибка при сохранении настроек'}
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center px-1 py-4 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-5 w-5 mr-2" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'llm' && renderLLMSettings()}
      {activeTab === 'system' && renderSystemSettings()}
      {activeTab === 'api' && renderApiSettings()}
    </div>
  );
}

export default SettingsPage;
