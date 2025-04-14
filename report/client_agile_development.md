# Agile Design for Client Side

## Introduction

The overall goal of the client side is to provide a text browser that interacts with the server via HTTP/1.1 protocol. Several specific demands has been identified.

### Obligatory specifications with top priority

- Support HTTP/1.1 GET, HEAD and POST methods. When calling these methods, the client should support HEX encoding of the URL. The client should also support keep-alive connections.
- On receiving a response with embedded objects, the client should get all the objects before presenting the page to the user.
- Basic authentication should be supported. Classic RFC 2109 cookies should also be supported for session management.
- Error handling for different HTTP status codes. The client should be able to redirect to a different URL if the server returns a 3xx status code. For other status codes, the client should display an error message to the user.
- Basic buffer management.

### Optional specifications

- Support HTTPS protocol.
- Compression of the response using gzip or deflate.
- User test file upload via POST method.
- Batch download of server text files.

## Use Cases

### Use Case 1: Basic Surfer

**Actors**: User, Client
**Preconditions**: The user has a working internet connection and the client is installed. A server is available and accessible.
**Postconditions**: The user can browse the server files.
**Main Flow**:

1. The user opens the client.
2. The user specifies the server URL as well as authentication information.
3. The client sends a GET request to the server for listing the accessible files, with the authentication information.
4. The server responds with a list of files.
5. The user selects a file from the list to view.
6. The client sends a GET request to the server for the selected file.
7. The server responds with the file content.
8. The client displays the file content to the user.
9. The user finishes browsing and closes the client.

**Alternative Flows**:

- If the server returns a 3xx status code, the client redirects to the new URL.
- If the server returns a 4xx or 5xx status code, the client displays a predefined error message to the user.
- If the server returns an unexpected status code, the client displays an error message to the user.

### Use Case 2: Client Configuration

**Actors**: User, Client
**Preconditions**: The user has a working internet connection and the client is installed.
**Postconditions**: The user can configure the client settings.
**Main Flow**:

1. The user opens the client.
2. The user navigates to the settings menu, or presses a shortcut key.
3. The client displays the settings menu.
4. The user modifies the settings as desired (e.g., use keep-alive connections, enable/disable cookies, etc.).
5. The user saves the settings.
6. The client checks the validity of the settings and applies them.
7. The user closes the settings menu.
8. The user continues using the client with the new settings.

**Alternative Flows**:

- If the user cancels the settings menu, the client discards any changes made.
- If the user tries to save invalid settings, the client displays an error message and does not apply the changes.

### Use Case 3: File Upload

**Actors**: User, Client
**Preconditions**: The user has a working internet connection and the client is installed. A server is available and accessible.
**Postconditions**: The user can upload files to the server file system.
**Main Flow**:

1. The user opens the client.
2. The user specifies the server URL as well as authentication information.
3. The client sends a GET request to the server for listing the accessible files, with the authentication information.
4. The server responds with a list of files.
5. The user selects to upload a file and enters the file path.
6. The client checks the file path and sends a POST request to the server with the file content.
7. The server responds with a status code indicating success or failure of the upload.
8. The client displays a success or error message to the user.
9. The client updates the file list if the upload was successful.
10. The user finishes uploading and continues using the client.

**Alternative Flows**:

- If the server returns a 3xx status code, the client redirects to the new URL.
- If the server returns a error status code, the client displays a predefined error message to the user.
- If the server returns an unexpected status code, the client displays an error message to the user.
- If the file is already present on the server, the client prompts the user for an action (overwrite, skip, or rename).

### Use Case 4: Batch Download

**Actors**: User, Client
**Preconditions**: The user has a working internet connection and the client is installed. A server is available and accessible.
**Postconditions**: The user can download multiple files from the server.
**Main Flow**:

1. The user opens the client.
2. The user specifies the server URL as well as authentication information.
3. The client sends a GET request to the server for listing the accessible files, with the authentication information.
4. The server responds with a list of files.
5. The user selects multiple files from the list to download.
6. The client sends a GET request to the server for each selected file.
7. The server responds with the file content for each request.
8. The client saves the files to the user's local file system.
9. The client displays a success message to the user, as well as the location of the downloaded files.
10. The user finishes downloading and closes the client.

**Alternative Flows**:

- If the server returns a 3xx status code, the client redirects to the new URL.
- If the server returns an error status code, the client displays a predefined error message to the user.
- If the server returns an unexpected status code, the client displays an error message to the user.
- If the user cancels the download, the client stops the download process and displays a message to the user.

## Design