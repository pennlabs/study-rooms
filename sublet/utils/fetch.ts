import getCsrfTokenCookie from './csrf';

/**
 * Generic API request function.
 * @param {string} path - The URL endstring of the API endpoint.
 * @param {string} method - The HTTP method (e.g., 'GET', 'POST').
 * @param {Object} [headers] - Optional headers object.
 * @param {Object} [body] - Optional body object, must be provided for methods like POST.
 * @returns {Promise} - A promise that resolves to the response of the API call.
 */
async function apiRequest(path: string, method: string, body: any = null, headers: Record<string, string> = {}) {

  const username = process.env.NEXT_PUBLIC_API_USERNAME;
  const password = process.env.NEXT_PUBLIC_API_PASSWORD;
  const url = `${process.env.NEXT_PUBLIC_BASE_URL}/${path}/`

  const encodedCredentials = btoa(`${username}:${password}`);

  const csrfToken = getCsrfTokenCookie();

  if (!username || !password) {
    console.error('API credentials are not set in environment variables.');
    throw new Error('API credentials are missing.');
  }

  // Initialize the fetch options
  const options: RequestInit = {
    method: method,
    headers: new Headers({
      'Authorization': `Basic ${encodedCredentials}`,
      'X-CSRFToken': csrfToken,
      ...headers, // Spread any additional headers provided
    }),
  };

  // Determine if the body should be JSON or FormData
  if (body instanceof FormData) {
    // If the body is FormData, do not set 'Content-Type' header, the browser will set it with the correct boundary
    options.body = body;
  } else if (method !== 'GET' && body) {
    // For JSON, set 'Content-Type' to 'application/json' and stringify the body
    options.headers = new Headers({ 'Content-Type': 'application/json', ...headers });
    options.body = JSON.stringify(body);
  }

  // If the method is not 'GET' and the body is provided, add it to the options
  if (method !== 'GET' && body) {
    options.body = JSON.stringify(body);
  }

  // Perform the fetch request
  return fetch(url, options)
    .then(response => {
      // Check if the response is ok (status in the range 200-299)
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json(); // Parse JSON response
    })
    .catch(error => {
      console.error('There has been a problem with your fetch operation:', error);
      throw error; // Rethrow to allow further handling
    });
}

export default apiRequest