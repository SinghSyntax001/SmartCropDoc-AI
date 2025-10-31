/* ============== NAVIGATION MENU TOGGLE ============== */
const navLinks = document.getElementById("navLinks");

function showMenu() {
  navLinks.style.right = "0";
}

function hideMenu() {
  navLinks.style.right = "-200px";
}

/* ============== FILE UPLOAD HANDLING ============== */

// Initialize file upload handlers if on upload page
document.addEventListener("DOMContentLoaded", function () {
  const dropZone = document.getElementById("dropZone");
  const imageInput = document.getElementById("imageInput");

  if (dropZone && imageInput) {
    // Click to upload
    dropZone.addEventListener("click", () => imageInput.click());

    // File input change
    imageInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        previewImage(e.target.files[0]);
      }
    });

    // Drag and drop
    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.classList.add("drag-over");
    });

    dropZone.addEventListener("dragleave", () => {
      dropZone.classList.remove("drag-over");
    });

    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("drag-over");
      if (e.dataTransfer.files.length > 0) {
        imageInput.files = e.dataTransfer.files;
        previewImage(e.dataTransfer.files[0]);
      }
    });
  }

  // Load saved language preference
  const savedLanguage = localStorage.getItem("preferredLanguage");
  if (savedLanguage && document.getElementById("languageCode")) {
    document.getElementById("languageCode").value = savedLanguage;
  }
});

/**
 * Preview selected image
 */
function previewImage(file) {
  const preview = document.getElementById("imagePreview");
  const previewImg = document.getElementById("previewImg");
  const dropZone = document.getElementById("dropZone");

  if (preview && previewImg && file.type.startsWith("image/")) {
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      preview.style.display = "block";
      if (dropZone) dropZone.style.display = "none";
    };
    reader.readAsDataURL(file);
  }
}

/**
 * Clear selected image
 */
function clearImage() {
  const imageInput = document.getElementById("imageInput");
  const preview = document.getElementById("imagePreview");
  const dropZone = document.getElementById("dropZone");

  imageInput.value = "";
  if (preview) preview.style.display = "none";
  if (dropZone) dropZone.style.display = "block";
}

/**
 * Validate image file
 */
function validateImageFile(file) {
  const maxSize = 10 * 1024 * 1024; // 10MB

  if (!file) {
    return { valid: false, error: "Please select an image file" };
  }

  const allowedTypes = ["image/jpeg", "image/png"];
  if (!allowedTypes.includes(file.type)) {
    return { valid: false, error: "Only JPG and PNG files are supported" };
  }

  if (file.size > maxSize) {
    return { valid: false, error: "File size must be under 10MB" };
  }

  return { valid: true, error: null };
}

/* ============== FILE UPLOAD FORM HANDLING ============== */

/**
 * Handle file upload and API calls
 */
async function handleFileUpload() {
  const imageInput = document.getElementById("imageInput");
  const file = imageInput.files[0];

  // Validate file
  const validation = validateImageFile(file);
  if (!validation.valid) {
    showError(validation.error);
    return;
  }

  // Get language code
  const languageCode = document.getElementById("languageCode")?.value || "en";
  localStorage.setItem("preferredLanguage", languageCode);

  // Show loading state
  showLoading();

  try {
    // Create FormData
    const formData = new FormData();
    formData.append("image", file);
    formData.append("language_code", languageCode);

    // Make API call to predict-and-recommend endpoint
    const response = await fetch("/api/predict-and-recommend", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      showError(data.error || "Upload failed. Please try again");
      hideLoading();
      return;
    }

    // Display results
    displayResults(data);
    hideLoading();
  } catch (error) {
    console.error("Upload error:", error);
    showError("Something went wrong. Please refresh and try again");
    hideLoading();
  }
}

/* ============== RESULTS DISPLAY ============== */

/**
 * Display prediction and recommendation results
 */
function displayResults(data) {
  const resultsContainer = document.getElementById("resultsContainer");
  const diseaseName = document.getElementById("diseaseName");
  const confidenceValue = document.getElementById("confidenceValue");
  const severityValue = document.getElementById("severityValue");
  const severityBar = document.getElementById("severityBar");
  const qualityValue = document.getElementById("qualityValue");
  const gradcamImage = document.getElementById("gradcamImage");
  const recommendationText = document.getElementById("recommendationText");

  // Hide form and show results
  const form = document.querySelector(".upload-form");
  if (form) form.style.display = "none";

  // Set disease information
  const prediction = data.prediction;
  diseaseName.textContent = prediction.disease_name;
  confidenceValue.textContent = prediction.confidence.toFixed(2) + "%";
  severityValue.textContent = prediction.severity_level + "/5";
  qualityValue.textContent =
    prediction.image_quality.charAt(0).toUpperCase() +
    prediction.image_quality.slice(1);

  // Display severity bar
  displaySeverityBar(prediction.severity_level, severityBar);

  // Display Grad-CAM image
  if (prediction.gradcam_image) {
    gradcamImage.src = `data:image/png;base64,${prediction.gradcam_image}`;
    gradcamImage.style.display = "block";
  }

  // Format and display recommendation
  const recommendation = data.recommendation.recommendation;
  recommendationText.innerHTML = formatRecommendation(recommendation);

  // Store result data for download
  window.lastResultData = {
    prediction: prediction,
    recommendation: data.recommendation,
  };

  // Show results container
  resultsContainer.style.display = "block";
  resultsContainer.scrollIntoView({ behavior: "smooth" });
}

/**
 * Format recommendation text (parse markdown-like formatting)
 */
function formatRecommendation(text) {
  if (!text) return "";

  // Split by common section indicators
  let formatted = text;

  // Convert ** to strong
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Convert - to bullet points
  formatted = formatted
    .split("\n")
    .map((line) => {
      if (line.startsWith("-")) {
        return "<li>" + line.substring(1).trim() + "</li>";
      }
      return line;
    })
    .join("\n");

  // Wrap consecutive list items
  formatted = formatted.replace(/(<li>.*?<\/li>)/gs, "<ul>$&</ul>");
  formatted = formatted.replace(/<\/ul>\n<ul>/g, "");

  // Split into paragraphs
  formatted = formatted
    .split("\n\n")
    .map((para) => {
      if (para.trim().startsWith("<ul>")) {
        return para;
      }
      return "<p>" + para.trim() + "</p>";
    })
    .join("");

  return formatted;
}

/**
 * Display severity bar with color coding
 */
function displaySeverityBar(severity, barElement) {
  const severities = [0, 1, 2, 3, 4, 5];
  let color = "#4caf50"; // Green

  if (severity >= 4) {
    color = "#f44336"; // Red
  } else if (severity === 3) {
    color = "#ffc107"; // Yellow
  } else if (severity > 2) {
    color = "#ff9800"; // Orange
  }

  // Create visual bar
  const percentage = (severity / 5) * 100;
  barElement.style.width = percentage + "%";
  barElement.style.backgroundColor = color;
}

/* ============== LOADING & ERROR STATES ============== */

/**
 * Show loading spinner
 */
function showLoading() {
  const loadingContainer = document.getElementById("loadingContainer");
  const errorContainer = document.getElementById("errorContainer");
  const resultsContainer = document.getElementById("resultsContainer");

  if (loadingContainer) loadingContainer.style.display = "block";
  if (errorContainer) errorContainer.style.display = "none";
  if (resultsContainer) resultsContainer.style.display = "none";

  // Disable upload button
  const uploadBtn = document.getElementById("uploadBtn");
  if (uploadBtn) {
    uploadBtn.disabled = true;
    uploadBtn.style.opacity = "0.5";
  }
}

/**
 * Hide loading spinner
 */
function hideLoading() {
  const loadingContainer = document.getElementById("loadingContainer");
  if (loadingContainer) loadingContainer.style.display = "none";

  // Enable upload button
  const uploadBtn = document.getElementById("uploadBtn");
  if (uploadBtn) {
    uploadBtn.disabled = false;
    uploadBtn.style.opacity = "1";
  }
}

/**
 * Show error message
 */
function showError(message) {
  const errorContainer = document.getElementById("errorContainer");
  const errorMessage = document.getElementById("errorMessage");
  const loadingContainer = document.getElementById("loadingContainer");
  const resultsContainer = document.getElementById("resultsContainer");

  if (errorMessage) errorMessage.textContent = message;
  if (errorContainer) errorContainer.style.display = "block";
  if (loadingContainer) loadingContainer.style.display = "none";
  if (resultsContainer) resultsContainer.style.display = "none";

  // Disable upload button
  const uploadBtn = document.getElementById("uploadBtn");
  if (uploadBtn) {
    uploadBtn.disabled = false;
    uploadBtn.style.opacity = "1";
  }
}

/* ============== ACTION BUTTONS ============== */

/**
 * Download result as PDF/image report
 */
function downloadResult() {
  if (!window.lastResultData) return;

  const data = window.lastResultData;
  const prediction = data.prediction;
  const recommendation = data.recommendation;

  // Create a simple text report
  let report = "CropGuard AI - Disease Detection Report\n";
  report += "=====================================\n\n";

  report += `Disease: ${prediction.disease_name}\n`;
  report += `Confidence: ${prediction.confidence}%\n`;
  report += `Severity Level: ${prediction.severity_level}/5\n`;
  report += `Image Quality: ${prediction.image_quality}\n\n`;

  report += "Treatment Recommendation:\n";
  report += "-------------------------\n";
  report += recommendation.recommendation + "\n\n";

  report += `Generated on: ${recommendation.timestamp}\n`;
  report += "© 2025 CropGuard AI\n";

  // Create blob and download
  const blob = new Blob([report], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `cropguard_report_${Date.now()}.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Reset form and upload another image
 */
function uploadAnother() {
  clearImage();

  const resultsContainer = document.getElementById("resultsContainer");
  const errorContainer = document.getElementById("errorContainer");
  const form = document.querySelector(".upload-form");
  const uploadBtn = document.getElementById("uploadBtn");

  if (resultsContainer) resultsContainer.style.display = "none";
  if (errorContainer) errorContainer.style.display = "none";
  if (form) form.style.display = "block";
  if (uploadBtn) {
    uploadBtn.disabled = false;
    uploadBtn.style.opacity = "1";
  }

  // Scroll to top
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/**
 * Reset the entire form
 */
function resetForm() {
  clearImage();

  const errorContainer = document.getElementById("errorContainer");
  const form = document.querySelector(".upload-form");

  if (errorContainer) errorContainer.style.display = "none";
  if (form) form.style.display = "block";
}

/* ============== LOGIN PAGE FUNCTIONS ============== */

/**
 * Handle login form submission (placeholder)
 */
function handleLogin(event) {
  event.preventDefault();

  const email = document.getElementById("email")?.value;
  const password = document.getElementById("password")?.value;
  const rememberMe = document.getElementById("rememberMe")?.checked;

  if (!email || !password) {
    showLoginError("Please fill in all fields");
    return;
  }

  // TODO: Implement actual login API call
  console.log("Login attempt:", { email, rememberMe });
  showLoginError("Login feature coming soon!");
}

/**
 * Show login error message
 */
function showLoginError(message) {
  const errorElement = document.getElementById("loginError");
  if (errorElement) {
    errorElement.textContent = message;
    errorElement.style.display = "block";
  }
}

/**
 * Edit profile (placeholder)
 */
function editProfile() {
  alert("Profile editing coming soon!");
}

/* ============== UTILITY FUNCTIONS ============== */

/**
 * Format date for display
 */
function formatDate(date) {
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
