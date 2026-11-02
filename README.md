# Instagram Hide Followers & Following Lists

<p align="center">
  A lightweight Python utility to enable Instagram's hidden followers and following lists privacy setting through its private GraphQL API.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Dependencies-None-success" />
  <img src="https://img.shields.io/badge/API-Instagram-purple" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
</p>

---

## Overview

This project enables Instagram's `hide_followers_following_list` account privacy setting using an authenticated request to Instagram's private GraphQL API.

It uses your Instagram `sessionid` cookie for authentication, validates the session, executes the privacy mutation, and verifies Instagram's response before reporting success.

## Features

- **Privacy Setting:** Enables hidden followers and following lists.
- **Session Authentication:** Uses your Instagram session ID.
- **Automatic User ID Extraction:** Extracts the numeric user ID from the session.
- **Hidden Input:** Uses `getpass` to prevent session IDs from appearing in the terminal.
- **Session Validation:** Rejects invalid or incorrectly formatted session IDs.
- **Structured Architecture:** Uses a frozen `Session` dataclass.
- **Custom Exceptions:** Separate validation, Instagram, and general errors.
- **Credential Protection:** Redacts sensitive authentication data from HTTP error messages.
- **Redirect Protection:** Blocks HTTP redirects to prevent credential forwarding.
- **Response Validation:** Confirms the API returned `value=true`.
- **Logging:** Provides structured terminal error and status messages.
- **No Dependencies:** Uses only Python's standard library.

## Installation

Clone the repository:

```bash
git clone https://github.com/DudeGeorgesTG/Instagram-Hide-Followers-Following-Lists.git
```

Enter the project directory:

```bash
cd Instagram-Hide-Followers-Following-Lists
```

## Requirements

- Python 3.10 or newer
- Instagram account
- Valid Instagram `sessionid` cookie
- Internet connection

No external Python packages are required.

## Usage

Run the script:

```bash
python main.py
```

Enter your Instagram session ID when prompted:

```text
Your Instagram sessionid value:
```

Paste only the session cookie value.

Do not include `sessionid=`.

Your input will remain hidden while typing.

## Example Output

**Successful execution**

```text
INFO: Instagram confirmed the setting (value=true).
Enabled: Instagram returned value=true.
```

**Invalid session**

```text
ERROR: Invalid sessionid format: expected a numeric user ID followed by ':' or '%3A'.
```

**Network error**

```text
ERROR: Network/TLS failure: ...
```

**Instagram API error**

```text
ERROR: HTTP 400: ...
```

## How It Works

1. Requests the Instagram session ID using hidden terminal input.
2. Validates the session ID format.
3. Extracts the numeric Instagram user ID.
4. Creates a structured `Session` instance.
5. Generates the authentication token using Base64-encoded JSON.
6. Constructs an authenticated GraphQL POST request.
7. Sends the privacy mutation to Instagram.
8. Processes and validates the API response.
9. Reports success only if Instagram confirms `value=true`.

## API Details

| Parameter | Value |
|---|---|
| Endpoint | `https://i.instagram.com/graphql/query` |
| HTTP Method | POST |
| Mutation | `IGSettingsBooleanMutation` |
| Setting ID | `hide_followers_following_list` |
| Setting Value | `true` |
| Callsite | `account_privacy` |
| Authentication | `Bearer IGT:2` |
| App ID | `124024574287414` |
| Request Timeout | 15 seconds |

## Project Structure

```text
Instagram-Hide-Followers-Following-Lists/
│
├── main.py
└── README.md
```

## Architecture

The project uses a modular structure with dedicated functions for each responsibility.

| Component | Responsibility |
|---|---|
| `Session` | Session validation and authentication |
| `_build_request()` | Constructs the GraphQL request |
| `_redact()` | Removes sensitive credentials from error messages |
| `_extract_error_details()` | Extracts selected API error information |
| `_http_error()` | Handles HTTP errors |
| `_execute()` | Executes the HTTP request |
| `_is_success()` | Validates Instagram's response |
| `hide_lists()` | Main privacy-setting operation |
| `main()` | CLI entry point and logging configuration |

### Exception Handling

```python
HideListsError
├── ValidationError
└── InstagramError
```

### Exit Codes

| Exit Code | Description |
|---|---|
| `0` | Operation successful |
| `1` | Instagram, network, or request error |
| `2` | Session validation error |
| `130` | Interrupted by user |

## Security

Your Instagram session ID is sensitive authentication information.

This project includes several security measures:

- Hidden session ID input.
- Credential redaction in HTTP error messages.
- HTTP redirect blocking.
- No session storage or file logging.
- Response size limits.
- Request timeout protection.
- No automatic retries.

**Never share your session ID or commit it to a public repository.**

## Disclaimer

This project is intended for educational and research purposes.

It interacts with Instagram's private and undocumented GraphQL API. Instagram may change its endpoints, authentication requirements, mutation identifiers, or privacy settings without notice.

Use at your own risk.

This project is not affiliated with, maintained by, or endorsed by Instagram or Meta.

---

<p align="center">
  Developed by <a href="https://github.com/DudeGeorgesTG">DudeGeorgesTG</a>
</p>
