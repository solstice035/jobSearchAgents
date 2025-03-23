import React, { useState } from 'react';
import { Job, analyzeResumeMatch, ResumeMatchResponse } from '../../services/job-search';

interface ResumeMatchModalProps {
  job: Job | null;
  isOpen: boolean;
  onClose: () => void;
  userResume?: string;
}

const ResumeMatchModal: React.FC<ResumeMatchModalProps> = ({
  job,
  isOpen,
  onClose,
  userResume,
}) => {
  const [resumeText, setResumeText] = useState<string>(userResume || '');
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [matchResult, setMatchResult] = useState<ResumeMatchResponse | null>(null);

  if (!isOpen || !job) {
    return null;
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setResumeFile(file);
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setResumeText(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate inputs
    if (!resumeFile && !resumeText.trim()) {
      setError('Please provide a resume file or paste resume text');
      return;
    }
    
    if (!job.full_text) {
      setError('Job description is missing');
      return;
    }
    
    // Clear previous error and results
    setError(null);
    setMatchResult(null);
    
    try {
      setIsLoading(true);
      
      const result = await analyzeResumeMatch({
        job_description: job.full_text,
        resume_text: resumeText.trim() || undefined,
        resume_file: resumeFile || undefined,
      });
      
      setMatchResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during analysis');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-10 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" onClick={onClose}></div>

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

        <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
          <div className="absolute top-0 right-0 pt-4 pr-4">
            <button
              type="button"
              className="bg-white rounded-md text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              onClick={onClose}
            >
              <span className="sr-only">Close</span>
              <svg className="h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div>
            <div className="mt-3 text-center sm:mt-0 sm:text-left">
              <h3 className="text-lg leading-6 font-medium text-gray-900" id="modal-title">
                Analyze Resume Match: {job.title || 'Job Position'}
              </h3>
              
              <div className="mt-2">
                <p className="text-sm text-gray-500">
                  Upload your resume or paste the text to see how well it matches this job opportunity.
                </p>
              </div>
              
              {matchResult ? (
                <div className="mt-4">
                  <div className="mb-4 flex justify-center">
                    <div className="inline-flex items-center justify-center h-24 w-24 rounded-full bg-blue-100">
                      <span className="text-2xl font-bold text-blue-800">
                        {matchResult.match_score}%
                      </span>
                    </div>
                  </div>
                  
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Analysis</h4>
                  <div className="bg-gray-50 p-3 rounded-md text-sm text-gray-700 max-h-60 overflow-y-auto">
                    {matchResult.analysis.split('\n').map((line, index) => (
                      <p key={index} className={index > 0 ? 'mt-2' : ''}>
                        {line}
                      </p>
                    ))}
                  </div>
                  
                  <div className="mt-4 flex justify-end">
                    <button
                      type="button"
                      className="ml-3 inline-flex justify-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      onClick={onClose}
                    >
                      Close
                    </button>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="mt-4">
                  <div className="mb-4">
                    <label htmlFor="resumeFile" className="block text-sm font-medium text-gray-700 mb-1">
                      Upload Resume
                    </label>
                    <input
                      type="file"
                      id="resumeFile"
                      accept=".pdf,.doc,.docx,.txt"
                      onChange={handleFileChange}
                      className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full text-sm text-gray-900 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                  </div>
                  
                  <div className="mb-4">
                    <label htmlFor="resumeText" className="block text-sm font-medium text-gray-700 mb-1">
                      Or Paste Resume Text
                    </label>
                    <textarea
                      id="resumeText"
                      value={resumeText}
                      onChange={handleTextChange}
                      rows={10}
                      className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="Paste your resume text here..."
                    ></textarea>
                  </div>
                  
                  {error && (
                    <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md text-sm">
                      {error}
                    </div>
                  )}
                  
                  <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                    <button
                      type="submit"
                      disabled={isLoading}
                      className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isLoading ? 'Analyzing...' : 'Analyze Match'}
                    </button>
                    <button
                      type="button"
                      className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:w-auto sm:text-sm"
                      onClick={onClose}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResumeMatchModal;
