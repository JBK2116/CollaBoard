function closePopup() {
  document.getElementById("errorPopup").style.display = "none";
}

function closeExpiredPopup() {
  document.getElementById("expiredPopup").style.display = "none";
}

// Auto-close popups after 5 seconds
document.addEventListener("DOMContentLoaded", function () {
  const errorPopup = document.getElementById("errorPopup");
  const expiredPopup = document.getElementById("expiredPopup");

  if (errorPopup) {
    setTimeout(function () {
      errorPopup.style.display = "none";
    }, 5000);
  }

  if (expiredPopup) {
    setTimeout(function () {
      expiredPopup.style.display = "none";
    }, 5000);
  }
});
