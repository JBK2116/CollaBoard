/**
 * Meeting Summary Page Functionality
 * Handles meeting summarization and export with theme-consistent UI
 */

document.addEventListener("DOMContentLoaded", function () {
  // ======================
  // 1. INITIAL SETUP
  // ======================
  const pathParts = window.location.pathname.split("/");
  const meetingId = pathParts[2]; // Extract UUID from URL

  // Get DOM elements
  const generateBtn = document.getElementById("generate-btn");
  const exportBtn = document.getElementById("export-btn")
  const container = document.querySelector(".container");

  // ======================
  // 2. UI COMPONENTS
  // ======================

  /**
   * Show temporary popup notification
   * @param {string} message - Text to display
   * @param {boolean} isError - Whether to show error style
   */
  function showPopup(message, isError = false) {
    const popup = document.createElement("div");
    popup.className = `custom-popup ${isError ? "error" : "success"}`;
    popup.textContent = message;
    document.body.appendChild(popup);

    setTimeout(() => {
      popup.classList.add("fade-out");
      setTimeout(() => popup.remove(), 300);
    }, 3000);
  }

  /**
   * Toggle loading state for the page
   * @param {boolean} isLoading - Whether to show loading state
   */
  function setLoadingState(isLoading) {
    if (isLoading) {
      const overlay = document.createElement("div");
      overlay.className = "loading-overlay";
      overlay.innerHTML = `
                <div class="loading-spinner"></div>
                <p class="loading-text">Processing...</p>
            `;
      document.body.appendChild(overlay);
      container.style.pointerEvents = "none";
      container.style.opacity = "0.7";
    } else {
      const overlay = document.querySelector(".loading-overlay");
      if (overlay) overlay.remove();
      container.style.pointerEvents = "auto";
      container.style.opacity = "1";
    }
  }

  /**
   * Show export format selection modal
   */
  function showExportOptions() {
    const modal = document.createElement("div");
    modal.className = "export-modal";
    modal.innerHTML = `
            <div class="modal-content">
                <h3 class="modal-title">Export Format</h3>
                <div class="format-option" data-format="pdf">
                    <svg viewBox="0 0 24 24" width="24" height="24">
                        <path fill="currentColor" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
                        <path fill="currentColor" d="M14 2v6h6m-4 5H8m8 4H8m2-8H8"/>
                    </svg>
                    PDF
                </div>
                <div class="format-option" data-format="docx">
                    <svg viewBox="0 0 24 24" width="24" height="24">
                        <path fill="currentColor" d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
                        <path fill="currentColor" d="M14 2v6h6m-2.5 4H10m5 4H10m5 4H10"/>
                    </svg>
                    Microsoft Word
                </div>
                <div class="format-option" data-format="gdoc">
                    <svg viewBox="0 0 24 24" width="24" height="24">
                        <path fill="currentColor" d="M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2zm0 16H5V5h14v14z"/>
                        <path fill="currentColor" d="M8 12h8v2H8zm0 4h8v2H8zm0-8h4v2H8z"/>
                    </svg>
                    Google Doc
                </div>
                <div class="cancel-export">Cancel</div>
            </div>
        `;
    document.body.appendChild(modal);

    // Event listeners for modal
    modal
      .querySelector(".cancel-export")
      .addEventListener("click", () => modal.remove());

    modal.querySelectorAll(".format-option").forEach((option) => {
      option.addEventListener("click", () => {
        modal.remove();
        handleExport(option.dataset.format);
      });
    });
  }

  // ======================
  // 3. API HANDLERS
  // ======================

  /**
   * Handle meeting summarization
   */
  async function handleSummarize() {
    setLoadingState(true);
    try {
      const response = await fetch(`/api/${meetingId}/summarize/`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
      });

      const data = await response.json();

      if (data.type === "error") {
        showPopup("Error summarizing meeting", true);
      } else {
        showPopup("Meeting successfully summarized, ready to be exported");
        exportBtn.disabled = false;
      }
    } catch (error) {
      showPopup("Network error - please try again", true);
      console.error("Summarize error:", error);
    } finally {
      setLoadingState(false);
    }
  }

  /**
   * Handle meeting export
   * @param {string} format - Export format (pdf/docx/gdoc)
   */
  async function handleExport(format) {
    setLoadingState(true);
    try {
      const response = await fetch(`/api/${meetingId}/export/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({ type: format }),
      });

      const data = await response.json();

      if (data.type === "error") {
        if (data.message.includes("not summarized")) {
          showPopup(
            "Cannot export - meeting has not been summarized yet",
            true
          );
        } else {
          showPopup("Export failed: " + data.message, true);
        }
      } else if (data.download_url) {
        window.location.href = data.download_url;
      }
    } catch (error) {
      showPopup("Export failed - please try again", true);
      console.error("Export error:", error);
    } finally {
      setLoadingState(false);
    }
  }

  // ======================
  // 4. HELPER FUNCTIONS
  // ======================

  /**
   * Get CSRF token for Django
   * @returns {string} CSRF token
   */
  function getCSRFToken() {
    return document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
  }

  // ======================
  // 5. EVENT LISTENERS
  // ======================
  generateBtn.addEventListener("click", handleSummarize);
  exportBtn.addEventListener("click", showExportOptions);

  // ======================
  // 6. DYNAMIC STYLES
  // ======================
  const style = document.createElement("style");
  style.textContent = `
        /* POPUP STYLES */
        .custom-popup {
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            padding: 12px 24px;
            border-radius: 12px;
            color: white;
            z-index: 1000;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            animation: slideIn 0.3s ease-out;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            font-weight: 500;
            font-size: 0.95rem;
            max-width: 90%;
            text-align: center;
        }
        .custom-popup.success {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .custom-popup.error {
            background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%);
        }
        .custom-popup.fade-out {
            animation: fadeOut 0.3s ease-out forwards;
        }
        
        /* LOADING OVERLAY */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255,255,255,0.85);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            z-index: 999;
            backdrop-filter: blur(2px);
        }
        .loading-spinner {
            border: 4px solid rgba(102, 126, 234, 0.2);
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin-bottom: 16px;
        }
        .loading-text {
            color: #2d3748;
            font-size: 1.1rem;
            font-weight: 500;
        }
        
        /* EXPORT MODAL */
        .export-modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1001;
            animation: fadeIn 0.2s ease-out;
        }
        .modal-content {
            background: white;
            padding: 24px;
            border-radius: 16px;
            width: 320px;
            max-width: 90%;
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        }
        .modal-title {
            margin-top: 0;
            margin-bottom: 20px;
            color: #2d3748;
            font-size: 1.3rem;
            text-align: center;
        }
        .format-option, .cancel-export {
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
        }
        .format-option {
            background: #f8fafc;
            color: #2d3748;
            font-weight: 500;
        }
        .format-option svg {
            margin-right: 12px;
            color: #667eea;
        }
        .format-option:hover {
            background: #edf2f7;
            transform: translateY(-1px);
        }
        .cancel-export {
            color: #718096;
            margin-top: 16px;
            font-size: 0.9rem;
        }
        .cancel-export:hover {
            background: #f8fafc;
        }
        
        /* ANIMATIONS */
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes slideIn {
            from { top: 0; opacity: 0; }
            to { top: 20px; opacity: 1; }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    `;
  document.head.appendChild(style);
});
