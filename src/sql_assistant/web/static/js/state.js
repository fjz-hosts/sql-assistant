/**
 * Application State Management
 */
const state = {
    llmConfigs: [],
    dbConfigs: [],
    activeLLM: '',
    activeDB: '',
    editingLLM: null,
    editingDB: null,
    schemaLoaded: false,
    schemaError: '',
    tableCount: 0,
    currentConversationId: null,
    conversations: [],
    llmModels: {},
    streamingEnabled: false,
    pendingPageChange: null,
    pendingQuestion: '',
};

// DOM Elements Helper
const $ = (id) => document.getElementById(id);

const dom = {
    chatMessages: $('chat-messages'),
    queryInput: $('query-input'),
    queryForm: $('query-form'),
    btnSend: $('btn-send'),
    historyList: $('history-list'),
    connectionStatus: $('connection-status'),
    settingsModal: $('settings-modal'),

    llmConfigList: $('llm-config-list'),
    llmForm: $('llm-form'),
    dbConfigList: $('db-config-list'),
    dbForm: $('db-form'),
};

// Expose state and helpers
window.state = state;
window.$ = $;
window.dom = dom;