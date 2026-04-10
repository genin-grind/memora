const PYTHON_SERVICE_URL =
  process.env.PYTHON_SERVICE_URL || "http://localhost:8000";

export async function pythonRequest(path, options = {}) {
  try {
    const response = await fetch(`${PYTHON_SERVICE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    const data = await response.json();

    if (!response.ok) {
      return {
        ok: false,
        status: response.status,
        data: {
          ...data,
          message: data?.message || data?.detail || "Python service request failed",
        },
      };
    }

    return {
      ok: true,
      status: response.status,
      data,
    };
  } catch (_error) {
    return {
      ok: false,
      status: 503,
      data: {
        message:
          "Python service is unreachable. Start the FastAPI service to use live backend features.",
      },
    };
  }
}
