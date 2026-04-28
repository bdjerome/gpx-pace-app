import axios from 'axios'

/**
 * A minimal Axios instance used exclusively for auth endpoints
 * (/auth/login, /auth/refresh, /auth/logout, /auth/register).
 *
 * It has NO request/response interceptors so auth calls are never silently
 * retried — this prevents infinite refresh loops. withCredentials is required
 * so the browser automatically sends and receives the HttpOnly refresh-token
 * cookie.
 */
const authClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
  withCredentials: true,
})

export default authClient
