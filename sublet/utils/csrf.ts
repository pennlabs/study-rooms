/**
 * @returns {string} The CSRF token used by the Django REST Framework
 */
export default function getCsrfTokenCookie() {
  let cookieValue = "";
  const csrfTokenName = "csrftoken";

  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the CSRF token name we want?
      if (cookie.startsWith(csrfTokenName + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(csrfTokenName.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}