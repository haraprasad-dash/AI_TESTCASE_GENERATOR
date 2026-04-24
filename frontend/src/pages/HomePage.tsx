import { useEffect, useState } from 'react';
import { 
  Beaker, Settings, Sparkles, FileText, 
  Upload, Zap, ArrowRight
} from 'lucide-react';
import { InputSection } from '../components/InputSection';
import { AIConfigSection } from '../components/AIConfigSection';
import { PromptSection } from '../components/PromptSection';
import { OutputPreview } from '../components/OutputPreview';
import { SettingsModal } from '../components/SettingsModal';
import { ReviewSection } from '../components/ReviewSection';
import { ReviewOutput } from '../components/ReviewOutput';
import { api } from '../services/api';
import toast from 'react-hot-toast';
import { useSettingsStore } from '../store/settingsStore';
import type {
  FileInput,
  GenerationInputs,
  GenerationConfiguration,
  GenerationResponse,
  ReviewInputs,
  ReviewConfiguration,
  ReviewResponse,
} from '../types';

export const HomePage: React.FC = () => {
  const defaultProvider = useSettingsStore((s) => s.llm.defaultProvider);
  const defaultGroqModel = useSettingsStore((s) => s.llm.groq.defaultModel);
  const defaultGroqTemperature = useSettingsStore((s) => s.llm.groq.defaultTemperature);
  const defaultOllamaModel = useSettingsStore((s) => s.llm.ollama.defaultModel);
  const groqFallbackModel = defaultGroqModel || 'llama-3.3-70b-versatile';

  const isGroqRateLimitError = (message?: string) => {
    const m = (message || '').toLowerCase();
    return m.includes('rate limit') || m.includes('rate_limit_exceeded') || m.includes('error code: 429') || m.includes('tokens per day') || m.includes('tpd');
  };

  const friendlyGenerationError = (message?: string) => {
    if (provider === 'groq' && isGroqRateLimitError(message)) {
      return `Groq quota reached for model '${model}'. Retrying with '${groqFallbackModel}' or switch to Ollama.`;
    }
    return message || 'Generation failed';
  };

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRefreshingReview, setIsRefreshingReview] = useState(false);
  const [output, setOutput] = useState<GenerationResponse | null>(null);
  const [reviewOutput, setReviewOutput] = useState<ReviewResponse | null>(null);
  const [currentStep, setCurrentStep] = useState(1);
  
  // Form state
  const [jiraId, setJiraId] = useState('');
  const [jiraIds, setJiraIds] = useState<string[]>([]);
  const [valueEdgeId, setValueEdgeId] = useState('');
  const [valueEdgeIds, setValueEdgeIds] = useState<string[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<FileInput[]>([]);
  const [testPlanPrompt, setTestPlanPrompt] = useState('');
  const [testCasePrompt, setTestCasePrompt] = useState('');
  const [useTestPlanTemplate, setUseTestPlanTemplate] = useState(true);
  const [useTestCaseTemplate, setUseTestCaseTemplate] = useState(true);
  const initialProvider: 'groq' | 'ollama' = defaultProvider || 'groq';
  const [provider, setProvider] = useState<'groq' | 'ollama'>(initialProvider);
  const [model, setModel] = useState(
    initialProvider === 'groq'
      ? (defaultGroqModel || 'llama-3.3-70b-versatile')
      : (defaultOllamaModel || '')
  );
  const [temperature, setTemperature] = useState(
    initialProvider === 'groq' ? (defaultGroqTemperature ?? 0.2) : 0.2
  );
  const [clarificationConversation, setClarificationConversation] = useState<Array<{ questions: string[]; answer: string }>>([]);
  const [reviewClarificationConversation, setReviewClarificationConversation] = useState<Array<{ questions: string[]; answer: string }>>([]);
  const [reviewTestCases, setReviewTestCases] = useState(true);
  const [reviewUserGuide, setReviewUserGuide] = useState(true);
  const [testCaseReviewInstructions, setTestCaseReviewInstructions] = useState('');
  const [userGuideReviewInstructions, setUserGuideReviewInstructions] = useState('');
  const [reviewTestCaseFileIds, setReviewTestCaseFileIds] = useState<string[]>([]);
  const [userGuideDocumentFileIds, setUserGuideDocumentFileIds] = useState<string[]>([]);
  const [userGuideReferenceFileIds, setUserGuideReferenceFileIds] = useState<string[]>([]);

  const hasGenerationInput = Boolean(
    jiraIds.length > 0 ||
    valueEdgeIds.length > 0 ||
    jiraId.trim() ||
    valueEdgeId.trim() ||
    uploadedFiles.length > 0 ||
    testPlanPrompt.trim() ||
    testCasePrompt.trim()
  );

  useEffect(() => {
    const nextProvider: 'groq' | 'ollama' = defaultProvider || 'groq';
    setProvider(nextProvider);
    if (nextProvider === 'groq') {
      setModel(defaultGroqModel || 'llama-3.3-70b-versatile');
      setTemperature(defaultGroqTemperature ?? 0.2);
      return;
    }
    setModel(defaultOllamaModel || '');
    setTemperature(0.2);
  }, [defaultProvider, defaultGroqModel, defaultGroqTemperature, defaultOllamaModel]);

  // Keep welcome card stable while typing IDs to avoid layout-shift scroll jumps.
  const showWelcomeCard = !output && uploadedFiles.length === 0;

  const handleFileUpload = (file: FileInput) => {
    setUploadedFiles((prev) => [...prev, file]);
    setCurrentStep(2);
  };

  const handleRemoveFile = (fileId: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.file_id !== fileId));
    setReviewTestCaseFileIds((prev) => prev.filter((id) => id !== fileId));
    setUserGuideDocumentFileIds((prev) => prev.filter((id) => id !== fileId));
    setUserGuideReferenceFileIds((prev) => prev.filter((id) => id !== fileId));
  };

  const handleReviewFilesSelected = async (files: FileList, scope: 'test-cases' | 'user-guide-docs' | 'user-guide-reference') => {
    for (const file of Array.from(files)) {
      try {
        const response = await api.uploadFile(file);
        setUploadedFiles((prev) => [...prev, response.data]);
        if (scope === 'test-cases') {
          setReviewTestCaseFileIds((prev) => prev.includes(response.data.file_id) ? prev : [...prev, response.data.file_id]);
        } else if (scope === 'user-guide-docs') {
          setUserGuideDocumentFileIds((prev) => prev.includes(response.data.file_id) ? prev : [...prev, response.data.file_id]);
        } else {
          setUserGuideReferenceFileIds((prev) => prev.includes(response.data.file_id) ? prev : [...prev, response.data.file_id]);
        }
        toast.success(`Attached for review: ${file.name}`);
      } catch (error: any) {
        toast.error(error.response?.data?.detail || `Failed to attach ${file.name}`);
      }
    }
  };

  const handleClarificationFileUpload = async (files: File[]) => {
    for (const file of files) {
      try {
        const response = await api.uploadFile(file);
        setUploadedFiles((prev) => [...prev, response.data]);
        toast.success(`Attached for clarification: ${file.name}`);
      } catch (error: any) {
        toast.error(error.response?.data?.detail || `Failed to attach ${file.name}`);
      }
    }
  };

  const handleGenerate = async (clarificationAnswers?: unknown) => {
    if (!hasGenerationInput) {
      toast.error('Please provide at least one input source: ticket, document, or custom instructions');
      return;
    }

    setIsGenerating(true);
    setCurrentStep(3);
    
    try {
      const clarificationText = typeof clarificationAnswers === 'string'
        ? clarificationAnswers.trim()
        : '';
      const isClarificationFollowUp = clarificationText.length > 0;

      let nextConversation = isClarificationFollowUp ? clarificationConversation : [];
      if (isClarificationFollowUp) {
        const questions = output?.metadata?.clarification_questions || [];
        nextConversation = [...clarificationConversation, { questions, answer: clarificationText }];
        setClarificationConversation(nextConversation);
      } else if (clarificationConversation.length > 0) {
        // New generation request should not inherit prior clarification context.
        setClarificationConversation([]);
      }

      const conversationBlock = nextConversation.length > 0
        ? [
            'Clarification Conversation History:',
            ...nextConversation.map((entry, idx) => {
              const qText = entry.questions.length > 0
                ? entry.questions.map((q, qIdx) => `${qIdx + 1}. ${q}`).join('\n')
                : 'No explicit questions captured.';
              return `Round ${idx + 1}\nQuestions:\n${qText}\nAnswer:\n${entry.answer}`;
            })
          ].join('\n\n')
        : '';

      const resolvedPlanPrompt = [
        testPlanPrompt?.trim(),
        conversationBlock,
        clarificationText
          ? `User Clarification Responses:\n${clarificationText}`
          : ''
      ].filter(Boolean).join('\n\n');

      const resolvedCasePrompt = [
        testCasePrompt?.trim(),
        conversationBlock,
        clarificationText
          ? `User Clarification Responses:\n${clarificationText}`
          : ''
      ].filter(Boolean).join('\n\n');

      // Backward-compatible aggregate prompt for logic paths still reading custom_prompt.
      const resolvedPrompt = [resolvedPlanPrompt, resolvedCasePrompt].filter(Boolean).join('\n\n');

      const inputs: GenerationInputs = {
        jira_id: jiraIds[0] || jiraId || undefined,
        jira_ids: jiraIds.length > 0 ? jiraIds : undefined,
        valueedge_id: valueEdgeIds[0] || valueEdgeId || undefined,
        valueedge_ids: valueEdgeIds.length > 0 ? valueEdgeIds : undefined,
        files: uploadedFiles,
        custom_prompt: resolvedPrompt || undefined,
        test_plan_prompt: resolvedPlanPrompt || undefined,
        test_case_prompt: resolvedCasePrompt || undefined,
        use_test_plan_template: useTestPlanTemplate,
        use_test_case_template: useTestCaseTemplate,
      };

      const configuration: GenerationConfiguration = {
        provider,
        model,
        temperature,
        max_tokens: 4096,
        top_p: 0.9,
        frequency_penalty: 0.0,
        presence_penalty: 0.0,
      };

      const response = await api.generate(inputs, configuration);
      let finalResponse = response.data;

      // Auto-retry once on a fallback Groq model when selected model hits quota limits.
      if (
        response.data.status === 'failed' &&
        provider === 'groq' &&
        isGroqRateLimitError(response.data.error) &&
        model !== groqFallbackModel
      ) {
        toast('Groq quota reached on selected model. Retrying with fallback model...', { icon: '⏳' });
        const retryConfiguration: GenerationConfiguration = {
          ...configuration,
          model: groqFallbackModel,
          max_tokens: 900,
        };
        const retry = await api.generate(inputs, retryConfiguration);
        finalResponse = retry.data;
        if (retry.data.status === 'completed') {
          setModel(groqFallbackModel);
          toast.success(`Switched to ${groqFallbackModel} and completed generation.`);
        }
      }

      if (finalResponse.status === 'failed' && finalResponse.error) {
        finalResponse.error = friendlyGenerationError(finalResponse.error);
      }

      setOutput(finalResponse);
      
      if (finalResponse.status === 'completed') {
        if (finalResponse.metadata?.clarification_required) {
          toast('Clarification needed. Please answer the questions and regenerate.', { icon: '📝' });
        } else {
          toast.success('Generation complete! 🎉');
        }
      } else if (finalResponse.error) {
        toast.error(`Generation failed: ${finalResponse.error}`);
      }
    } catch (error: any) {
      const backendMessage =
        error?.response?.data?.error ||
        error?.response?.data?.detail ||
        (error?.code === 'ECONNABORTED' ? 'Generation request timed out. Please retry with a smaller scope or fewer inputs.' : null) ||
        error?.message ||
        'Generation failed';
      toast.error(friendlyGenerationError(backendMessage));
      console.error(error);
    } finally {
      setIsGenerating(false);
    }
  };

  const isTestCaseArtifact = (filename: string) => /\.(feature|xlsx|xls|txt|md)$/i.test(filename);
  const isGuideArtifact = (filename: string) => /\.(pdf|docx|txt|md)$/i.test(filename);

  const validateReviewRequest = (reviewMode: 'test-cases' | 'user-guide' | 'both') => {
    const includeTestCaseSection = reviewMode === 'test-cases' || reviewMode === 'both';
    const includeUserGuideSection = reviewMode === 'user-guide' || reviewMode === 'both';

    const testCaseInstructions = includeTestCaseSection ? testCaseReviewInstructions.trim() : '';
    const userGuideInstructions = includeUserGuideSection ? userGuideReviewInstructions.trim() : '';

    const enableTestCaseTemplate = includeTestCaseSection && reviewTestCases;
    const enableUserGuideTemplate = includeUserGuideSection && reviewUserGuide;

    const hasTestCaseInstructionOnly = includeTestCaseSection && !enableTestCaseTemplate && Boolean(testCaseInstructions);
    const hasUserGuideInstructionOnly = includeUserGuideSection && !enableUserGuideTemplate && Boolean(userGuideInstructions);

    if (includeTestCaseSection && !enableTestCaseTemplate && !hasTestCaseInstructionOnly && reviewMode === 'test-cases') {
      toast.error('Enable Test Case template or provide Test Case Review Instructions');
      return false;
    }

    if (includeUserGuideSection && !enableUserGuideTemplate && !hasUserGuideInstructionOnly && reviewMode === 'user-guide') {
      toast.error('Enable User Guide template or provide User Guide Review Instructions');
      return false;
    }

    if (!enableTestCaseTemplate && !enableUserGuideTemplate && !hasTestCaseInstructionOnly && !hasUserGuideInstructionOnly) {
      toast.error('Please enable a review template or provide review instructions');
      return false;
    }

    if (enableTestCaseTemplate) {
      const hasTestCaseFiles = uploadedFiles.some((file) => isTestCaseArtifact(file.filename));
      if (!hasTestCaseFiles) {
        toast.error('Please attach test case files (.feature, .xlsx, .txt)');
        return false;
      }
    }

    if (includeUserGuideSection && (enableUserGuideTemplate || hasUserGuideInstructionOnly)) {
      const scopedGuideFiles = uploadedFiles.filter((file) => userGuideDocumentFileIds.includes(file.file_id));
      const hasGuideFiles = scopedGuideFiles.length > 0
        ? scopedGuideFiles.some((file) => isGuideArtifact(file.filename))
        : uploadedFiles.some((file) => isGuideArtifact(file.filename));
      if (!hasGuideFiles) {
        toast.error('Please attach user guide documents (.pdf, .docx, .txt, .md)');
        return false;
      }
    }

    return true;
  };

  const buildReviewPayload = (reviewMode: 'test-cases' | 'user-guide' | 'both'): { inputs: ReviewInputs; configuration: ReviewConfiguration } => {
    const includeTestCaseReview = reviewMode === 'test-cases' || reviewMode === 'both';
    const includeUserGuideReview = reviewMode === 'user-guide' || reviewMode === 'both';
    const testCaseInstructions = includeTestCaseReview ? testCaseReviewInstructions.trim() : '';
    const userGuideInstructions = includeUserGuideReview ? userGuideReviewInstructions.trim() : '';

    const useTestCaseTemplate = includeTestCaseReview && reviewTestCases;
    const useUserGuideTemplate = includeUserGuideReview && reviewUserGuide;

    const mergedInstructions = [
      includeTestCaseReview && testCaseInstructions
        ? `Test Case Review Instructions:\n${testCaseInstructions}`
        : '',
      includeUserGuideReview && userGuideInstructions
        ? `User Guide Review Instructions:\n${userGuideInstructions}`
        : '',
    ].filter(Boolean).join('\n\n');

    return {
      inputs: {
        jira_id: jiraIds[0] || jiraId || undefined,
        jira_ids: jiraIds.length > 0 ? jiraIds : undefined,
        valueedge_id: valueEdgeIds[0] || valueEdgeId || undefined,
        valueedge_ids: valueEdgeIds.length > 0 ? valueEdgeIds : undefined,
        files: uploadedFiles,
        custom_instructions: mergedInstructions || undefined,
        test_case_review_instructions: includeTestCaseReview && testCaseInstructions ? testCaseInstructions : undefined,
        user_guide_review_instructions: includeUserGuideReview && userGuideInstructions ? userGuideInstructions : undefined,
        review_test_cases: useTestCaseTemplate,
        review_user_guide: useUserGuideTemplate,
        clarification_history: reviewClarificationConversation,
      },
      configuration: {
        provider,
        model,
        temperature,
      },
    };
  };

  const runReview = async (
    mode: 'test-cases' | 'user-guide' | 'both',
    clarificationAnswer?: string,
  ) => {
    if (!validateReviewRequest(mode)) {
      return;
    }

    setIsGenerating(true);
    try {
      const answer = (clarificationAnswer || '').trim();
      let nextHistory = answer ? reviewClarificationConversation : [];

      if (answer) {
        const currentQuestions = reviewOutput?.metadata?.clarification_questions || [];
        nextHistory = [...reviewClarificationConversation, { questions: currentQuestions, answer }];
        setReviewClarificationConversation(nextHistory);
      }

      const payload = buildReviewPayload(mode);
      payload.inputs.clarification_history = nextHistory;

      const response = mode === 'test-cases'
        ? await api.reviewTestCases(payload.inputs, payload.configuration)
        : mode === 'user-guide'
        ? await api.reviewUserGuide(payload.inputs, payload.configuration)
        : await api.reviewBoth(payload.inputs, payload.configuration);

      setReviewOutput(response.data);
      if (response.data.status === 'clarification_required') {
        toast('Clarification needed. Partial results are available.', { icon: '📝' });
      } else {
        toast.success('Review completed');
      }
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Review failed');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReviewTestCases = async () => {
    await runReview('test-cases');
  };

  const handleReviewUserGuide = async () => {
    await runReview('user-guide');
  };

  const handleRunBothReviews = async () => {
    await runReview('both');
  };

  const handleReviewClarificationSubmit = async (answer: string) => {
    const reviewType = reviewOutput?.metadata?.review_type || 'both';
    await runReview(reviewType, answer);
  };

  const handleReviewClarificationFileUpload = async (files: File[]) => {
    for (const file of files) {
      const uploaded = await api.uploadFile(file);
      setUploadedFiles((prev) => [...prev, uploaded.data]);
      if (reviewOutput?.review_id) {
        await api.attachReviewClarificationFile(reviewOutput.review_id, file);
      }
    }
  };

  const refreshReviewStatus = async () => {
    if (!reviewOutput) return;
    setIsRefreshingReview(true);
    try {
      const status = await api.reviewStatus(reviewOutput.review_id);
      setReviewOutput(status.data);
      toast.success(`Review status: ${status.data.status}`);
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      if (error?.response?.status === 404) {
        toast.error('Review session not found. Please rerun review from the buttons above.');
      } else {
        toast.error(detail || 'Failed to refresh review status');
      }
    } finally {
      setIsRefreshingReview(false);
    }
  };

  const steps = [
    { num: 1, label: 'Input', desc: 'Add requirements' },
    { num: 2, label: 'Configure', desc: 'Set AI & review options' },
    { num: 3, label: 'Generate/Review', desc: 'Create or assess artifacts' },
  ];

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white/90 backdrop-blur-xl border-b border-white/20 sticky top-0 z-40">
        <div className="main-wrapper">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
                <Beaker className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">
                  TestGen <span className="gradient-text">AI</span>
                </h1>
                <p className="text-xs text-slate-500">Intelligent Test Generation & Review</p>
              </div>
            </div>

            <button
              onClick={() => setIsSettingsOpen(true)}
              className="btn-secondary"
            >
              <Settings className="w-4 h-4" />
              <span className="hidden sm:inline">Settings</span>
            </button>
          </div>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="bg-white/60 backdrop-blur-sm border-b border-white/20">
        <div className="main-wrapper">
          <div className="flex items-center justify-center">
            <div className="flex items-center gap-2 sm:gap-4">
              {steps.map((step, idx) => (
                <div key={step.num} className="flex items-center gap-2 sm:gap-4">
                  <div 
                    className={`flex flex-col sm:flex-row items-center gap-2 sm:gap-3 px-4 py-3 rounded-xl transition-all duration-300 cursor-pointer ${
                      currentStep >= step.num 
                        ? 'bg-blue-100 text-blue-700' 
                        : 'bg-slate-100 text-slate-400'
                    }`}
                    onClick={() => setCurrentStep(step.num)}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                      currentStep >= step.num 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-slate-300 text-slate-500'
                    }`}>
                      {step.num}
                    </div>
                    <div className="text-center sm:text-left">
                      <span className="block text-sm font-semibold">{step.label}</span>
                      <span className="hidden sm:block text-xs opacity-75">{step.desc}</span>
                    </div>
                  </div>
                  {idx < 2 && (
                    <ArrowRight className={`w-5 h-5 hidden md:block ${
                      currentStep > step.num ? 'text-blue-500' : 'text-slate-300'
                    }`} />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="main-wrapper">
        {isGenerating && (
          <div className="fixed bottom-6 right-6 z-50 bg-blue-600 text-white px-4 py-3 rounded-xl shadow-xl flex flex-col gap-1 max-w-xs">
            <div className="flex items-center gap-2">
              <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full flex-shrink-0" />
              <span className="text-sm font-medium">Generating... Please wait</span>
            </div>
          </div>
        )}

        {/* Welcome Card */}
        {showWelcomeCard && (
          <div className="content-card p-8 text-center mb-8 animate-fade-in">
            <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-xl shadow-blue-500/30">
              <Sparkles className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-slate-900 mb-3">
              Welcome to TestGen AI
            </h2>
            <p className="text-slate-600 max-w-xl mx-auto mb-8 text-lg">
              Generate test plans/cases and run review workflows with AI.
              Start by providing requirements from JIRA, ValueEdge, or uploading documents.
            </p>
            <div className="flex flex-wrap justify-center gap-6">
              <div className="flex items-center gap-2 text-slate-600 bg-slate-50 px-4 py-2 rounded-full">
                <FileText className="w-4 h-4 text-blue-500" /> 
                <span className="text-sm font-medium">JIRA Integration</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600 bg-slate-50 px-4 py-2 rounded-full">
                <Upload className="w-4 h-4 text-green-500" /> 
                <span className="text-sm font-medium">File Upload</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600 bg-slate-50 px-4 py-2 rounded-full">
                <Beaker className="w-4 h-4 text-indigo-500" />
                <span className="text-sm font-medium">Review Workflows</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600 bg-slate-50 px-4 py-2 rounded-full">
                <Zap className="w-4 h-4 text-amber-500" /> 
                <span className="text-sm font-medium">AI-Powered</span>
              </div>
            </div>
          </div>
        )}

        {/* Input Section */}
        <div className="content-card p-6 mb-6 animate-fade-in">
          <InputSection
            jiraId={jiraId}
            setJiraId={setJiraId}
            jiraIds={jiraIds}
            setJiraIds={setJiraIds}
            valueEdgeId={valueEdgeId}
            setValueEdgeId={setValueEdgeId}
            valueEdgeIds={valueEdgeIds}
            setValueEdgeIds={setValueEdgeIds}
            uploadedFiles={uploadedFiles}
            onFileUpload={handleFileUpload}
            onRemoveFile={handleRemoveFile}
          />
        </div>

        {/* Custom Prompt */}
        <div className="content-card p-6 mb-6 animate-fade-in">
          <PromptSection
            testPlanPrompt={testPlanPrompt}
            onTestPlanPromptChange={setTestPlanPrompt}
            testCasePrompt={testCasePrompt}
            onTestCasePromptChange={setTestCasePrompt}
            useTestPlanTemplate={useTestPlanTemplate}
            onUseTestPlanTemplateChange={setUseTestPlanTemplate}
            useTestCaseTemplate={useTestCaseTemplate}
            onUseTestCaseTemplateChange={setUseTestCaseTemplate}
            jiraIds={jiraIds}
            valueEdgeIds={valueEdgeIds}
            uploadedFiles={uploadedFiles}
            provider={provider}
            model={model}
          />
        </div>

        {/* AI Configuration */}
        <div className="content-card p-6 mb-6 animate-fade-in">
          <AIConfigSection
            provider={provider}
            setProvider={setProvider}
            model={model}
            setModel={setModel}
            temperature={temperature}
            setTemperature={setTemperature}
          />
        </div>

        <div className="content-card p-6 mb-6 animate-fade-in">
          <ReviewSection
            reviewTestCases={reviewTestCases}
            setReviewTestCases={setReviewTestCases}
            reviewUserGuide={reviewUserGuide}
            setReviewUserGuide={setReviewUserGuide}
            testCaseReviewInstructions={testCaseReviewInstructions}
            setTestCaseReviewInstructions={setTestCaseReviewInstructions}
            userGuideReviewInstructions={userGuideReviewInstructions}
            setUserGuideReviewInstructions={setUserGuideReviewInstructions}
            jiraIds={jiraIds}
            valueEdgeIds={valueEdgeIds}
            uploadedFiles={uploadedFiles}
            reviewTestCaseFileIds={reviewTestCaseFileIds}
            userGuideDocumentFileIds={userGuideDocumentFileIds}
            userGuideReferenceFileIds={userGuideReferenceFileIds}
            onTestCaseFilesSelected={(files) => handleReviewFilesSelected(files, 'test-cases')}
            onUserGuideDocumentsSelected={(files) => handleReviewFilesSelected(files, 'user-guide-docs')}
            onUserGuideReferenceFilesSelected={(files) => handleReviewFilesSelected(files, 'user-guide-reference')}
            onRemoveFile={handleRemoveFile}
            provider={provider}
            model={model}
          />
        </div>

        {/* Generate Button */}
        <div className="flex justify-center mb-8 animate-fade-in">
          <button
            onClick={() => handleGenerate()}
            disabled={isGenerating}
            className="btn-primary text-lg px-12 py-4"
          >
            {isGenerating ? (
              <>
                <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
                <span>Generating...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>Generate Test Plan & Cases</span>
              </>
            )}
          </button>
        </div>

        <div className="flex flex-wrap justify-center gap-3 mb-8 animate-fade-in">
          <button onClick={handleReviewTestCases} disabled={isGenerating} className="btn-primary px-6 py-3">
            Review Test Cases
          </button>
          <button onClick={handleReviewUserGuide} disabled={isGenerating} className="btn-primary px-6 py-3">
            Review User Guide
          </button>
          {reviewTestCases && reviewUserGuide && (
            <button onClick={handleRunBothReviews} disabled={isGenerating} className="btn-secondary px-6 py-3">
              Run Both Reviews
            </button>
          )}
        </div>

        {/* Output Preview */}
        {output && (
          <div className="content-card p-6 animate-fade-in">
            <OutputPreview
              output={output}
              onRefresh={() => handleGenerate()}
              isRefreshing={isGenerating}
              onSubmitClarification={(answers) => handleGenerate(answers)}
              onUploadClarificationFiles={handleClarificationFileUpload}
              clarificationHistory={clarificationConversation}
            />
          </div>
        )}

        {reviewOutput && (
          <div className="content-card p-6 mt-6 animate-fade-in">
            <ReviewOutput
              review={reviewOutput}
              onRefreshStatus={refreshReviewStatus}
              refreshing={isRefreshingReview}
              onSubmitClarification={handleReviewClarificationSubmit}
              onUploadClarificationFiles={handleReviewClarificationFileUpload}
              clarificationHistory={reviewClarificationConversation}
            />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="text-center py-8 text-white/70 text-sm">
        <p>© 2026 TestGen AI Agent. Powered by Advanced Language Models.</p>
      </footer>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </div>
  );
};
