const express = require('express');
const os = require('os');
const { exec } = require('child_process');
const path = require('path');

const app = express();
const PORT = 3000;

// Middleware for JSON and static files (if adding HTML later)
app.use(express.json());
app.use(express.static('public')); // Optional: For serving HTML/CSS if needed

// Helper: Get current user info
function getCurrentUserInfo() {
    const userInfo = os.userInfo();
    return {
        username: userInfo.username,
        uid: userInfo.uid || 'N/A (Windows uses SIDs)',
        homedir: userInfo.homedir,
        shell: userInfo.shell || 'cmd.exe (default)'
    };
}

// Helper: List system users (async for exec)
async function listSystemUsers() {
    return new Promise((resolve) => {
        exec('net user', (error, stdout, stderr) => {
            if (error) {
                resolve({ error: error.message });
                return;
            }
            const lines = stdout.split('\n');
            let usersSection = false;
            const users = [];
            const currentUser  = os.userInfo().username;

            lines.forEach(line => {
                const trimmed = line.trim();
                if (trimmed.includes('The command completed successfully')) {
                    usersSection = true;
                    return;
                }
                if (usersSection && trimmed && !trimmed.startsWith('---')) {
                    const userList = trimmed.split(/\s{2,}/).filter(u => u);
                    users.push(...userList);
                }
            });

            // Filter other users (exclude current)
            const otherUsers = users.filter(user => user && user !== currentUser );
            resolve({ users: otherUsers, total: otherUsers.length });
        });
    });
}

// Route 1: Home page - Shows current user info as HTML
app.get('/', async (req, res) => {
    const currentUser  = getCurrentUserInfo();
    const usersData = await listSystemUsers();

    let html = `
    <!DOCTYPE html>
    <html>
    <head><title>User Info Server</title></head>
    <body>
        <h1>Current User Info (via os module)</h1>
        <ul>
            <li>Username: ${currentUser .username}</li>
            <li>UID: ${currentUser .uid}</li>
            <li>Home Directory: ${currentUser .homedir}</li>
            <li>Shell: ${currentUser .shell}</li>
        </ul>
        <h2>Other System Users</h2>
        <p>Total other users: ${usersData.total || 0}</p>
        <ul>`;
    
    if (usersData.users) {
        usersData.users.forEach(user => {
            html += `<li>${user}</li>`;
        });
    } else if (usersData.error) {
        html += `<li>Error: ${usersData.error} (Try running server as admin)</li>`;
    }
    
    html += `
        </ul>
        <p><small>Server running on localhost:${PORT} | For JSON, visit /users</small></p>
    </body>
    </html>`;

    res.send(html);
});

// Route 2: API endpoint - Returns users as JSON
app.get('/users', async (req, res) => {
    const currentUser  = getCurrentUserInfo();
    const usersData = await listSystemUsers();

    res.json({
        currentUser ,
        otherUsers: usersData.users || [],
        totalOtherUsers: usersData.total || 0,
        note: usersData.error ? `Error: ${usersData.error}` : 'Run as admin for full list'
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
    console.log(`Visit http://localhost:${PORT}/ for HTML view`);
    console.log(`Visit http://localhost:${PORT}/users for JSON API`);
});
