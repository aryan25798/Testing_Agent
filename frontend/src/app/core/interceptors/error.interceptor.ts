import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMessage = 'An unexpected error occurred.';

      if (error.error instanceof ErrorEvent) {
        // Client-side / network error
        errorMessage = `Network Error: ${error.error.message}`;
      } else {
        // Server-side response error
        switch (error.status) {
          case 0:
            errorMessage = 'Cannot connect to backend server. Please verify the API is running at ' + req.url;
            break;
          case 400:
            errorMessage = error.error?.detail || error.error?.error || 'Bad Request: Invalid parameters supplied.';
            break;
          case 401:
            errorMessage = 'Authentication required. Please configure your API credentials.';
            break;
          case 403:
            errorMessage = error.error?.detail || 'Access forbidden: Insufficient permissions for this action.';
            break;
          case 404:
            errorMessage = error.error?.detail || 'The requested resource was not found.';
            break;
          case 413:
            errorMessage = 'Payload too large: The uploaded file or request exceeds size limits.';
            break;
          case 422:
            errorMessage = error.error?.detail?.[0]?.msg || 'Validation Error: Check input fields.';
            break;
          case 500:
            errorMessage = error.error?.detail || 'Internal Server Error: Backend encountered an unexpected fault.';
            break;
          case 503:
            errorMessage = 'Service Unavailable: AI Provider or third-party service is temporarily down.';
            break;
          default:
            errorMessage = `HTTP ${error.status}: ${error.statusText || error.message}`;
        }
      }

      console.error(`[API Error ${error.status}] ${req.method} ${req.url}:`, errorMessage, error);
      return throwError(() => new Error(errorMessage));
    })
  );
};
