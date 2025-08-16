const express = require('express');
const http = require('http');
const socketIo = require('socket.io');

const app = express();
const server = http.createServer(app);
const fs = require("fs");
const path = require("path");
const io = socketIo(server);

const PORT = process.env.SERVER_PORT;

const COLORS = ['Orange', 'Purple', 'Blue', 'Red', 'Green', 'Black'];       // Pool of colors
const chat_store = {};                              // Chat store to hold chat history per game
const games = {};                                   // Store active games and their participants
const activeAccusations = {};
const gameTimers = {};                              // To store timers for each game
const gameDuration = 300;                           // 5 mins
const users = {};                                   // Map user's socket.id and usernames
const botTimers = {};                               // Store bot response timers for each game

// LOGS:
// Set up logging to file
const LOG_FILE_PATH = '/usr/src/app/logs/logs_server_4.txt';
// Ensure the logs directory exists
try {
    if (!fs.existsSync('/usr/src/app/logs')) {
        fs.mkdirSync('/usr/src/app/logs', { recursive: true });
    }
} catch (err) {
    console.error('Error creating logs directory:', err);
}
// Function to write to log file
function writeToLog(level, message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${level}: ${message}\n`;
    
    fs.appendFile(LOG_FILE_PATH, logMessage, (err) => {
        if (err) {
            console.error('Error writing to log file:', err);
        }
    });
}
// Override console methods
const originalConsoleLog = console.log;
const originalConsoleDebug = console.debug;
const originalConsoleError = console.error;
console.log = function() {
    const message = Array.from(arguments).map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg) : arg
    ).join(' ');
    writeToLog('INFO', message);
    originalConsoleLog.apply(console, arguments);
};
console.debug = function() {
    const message = Array.from(arguments).map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg) : arg
    ).join(' ');
    writeToLog('DEBUG', message);
    originalConsoleDebug.apply(console, arguments);
};

console.error = function() {
    const message = Array.from(arguments).map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg) : arg
    ).join(' ');
    writeToLog('ERROR', message);
    originalConsoleError.apply(console, arguments);
};


// database:
games_table_created = false;
messages_table_created = false;
const sqlite3 = require("sqlite3").verbose();
const db = new sqlite3.Database("./database/turing.db", sqlite3.OPEN_READWRITE, (err) => {
    if (err) return console.error(err.message);
});
function createUsernamesTable(callback) {
    const sqlFilePath = path.join(__dirname, 'database', 'usernames.sql');
    fs.readFile(sqlFilePath, 'utf8', (readErr, sql) => {
        if (readErr) {
            console.error('--- DB: Error reading usernames.sql file:', readErr.message);
            return callback(readErr);
        }
        db.run(sql, (createErr) => {
            if (createErr) {
                console.error('--- DB: Error creating usernames table:', createErr.message);
                return callback(createErr);
            }
            console.log('--- DB: Usernames table created successfully.');
            callback();
        });
    });
}
function createGamesTable(callback) {
    const sqlFilePath = path.join(__dirname, 'database', 'games.sql');
    fs.readFile(sqlFilePath, 'utf8', (readErr, sql) => {
        if (readErr) {
            console.error('--- DB: Error reading games.sql file:', readErr.message);
            return callback(readErr);
        }
        db.run(sql, (createErr) => {
            if (createErr) {
                console.error('--- DB: Error creating games table:', createErr.message);
                return callback(createErr);
            }
            console.log('--- DB: Games table created successfully.');
            callback();
        });
    });
}
function createUsersandGamesTable(callback) {
    const sqlFilePath = path.join(__dirname, 'database', 'usersandgames.sql');
    fs.readFile(sqlFilePath, 'utf8', (readErr, sql) => {
        if (readErr) {
            console.error('--- DB: Error reading usersandgames.sql file:', readErr.message);
            return callback(readErr);
        }
        db.run(sql, (createErr) => {
            if (createErr) {
                console.error('--- DB: Error creating usersandgames table:', createErr.message);
                return callback(createErr);
            }
            console.log('--- DB: Usersandgames table created successfully.');
            callback();
        });
    });
}
const sql_check_username = `SELECT COUNT(*) AS count FROM usernames WHERE username = ?`;
const sql_insert_username = `
    INSERT INTO usernames (username)
    SELECT ?
    WHERE NOT EXISTS (SELECT 1 FROM usernames WHERE username = ?);
`;
const sql_update_start_time = `UPDATE games SET start_time = CURRENT_TIMESTAMP WHERE game_id = ?`;
const sql_update_end_time = `UPDATE games SET end_time = CURRENT_TIMESTAMP WHERE game_id = ?`;
const sql_get_game = `SELECT * FROM games WHERE game_id = ?`;
const sql_update_player1_accusation = `
    UPDATE games 
    SET player1_accusation_time = ?, player1_accused = ? 
    WHERE game_id = ?;
`;
const sql_update_player2_accusation = `
    UPDATE games 
    SET player2_accusation_time = ?, player2_accused = ? 
    WHERE game_id = ?;
`;
const sql_update_player_scores = `
    UPDATE games 
    SET player1_score = ?, player2_score = ?, bot_score = ?
    WHERE game_id = ?;
`;
const sql_update_user_score = `
    UPDATE usernames 
    SET score = score + ? 
    WHERE username = ? AND score = (
        SELECT score FROM usernames WHERE username = ?
    )
`;
const sql_get_leaderboard = `
    SELECT username, score 
    FROM usernames 
    ORDER BY score DESC
`;
function createMessagesTable(callback) {
    const sqlFilePath = path.join(__dirname, 'database', 'messages.sql');
    fs.readFile(sqlFilePath, 'utf8', (readErr, sql) => {
        if (readErr) {
            console.error('--- DB: Error reading messages.sql file:', readErr.message);
            return callback(readErr);
        }
        db.run(sql, (createErr) => {
            if (createErr) {
                console.error('--- DB: Error creating messages table:', createErr.message);
                return callback(createErr);
            }
            console.log('--- DB: Messages table created successfully.');
            callback();
        });
    });
}
const sql_insert_messages = `INSERT INTO messages(game_id, message_id, player_username, message_content, sent_time) VALUES (?, ?, ?, ?, ?)`;

async function initiateGame(username, game_id) {
    console.debug(`### INSIDE the initiateGame - game_id: ${game_id}`);

    try {
        const gameData = await new Promise((resolve, reject) => {
            db.get(sql_get_game, [game_id], (err, row) => {
                if (err) {
                    console.error('--- DB: Error fetching game data:', err.message);
                    return reject(err);
                }
                if (!row) {
                    console.error(`No game found with game_id: ${game_id}`);
                    return reject(new Error('Game not found'));
                }
                resolve(row);
            });
        });

        if (!gameData) {
            throw new Error(`Game data is null for game_id: ${game_id}`);
        }

        const { player1_username, player1_color, player2_username, player2_color, bot_color } = gameData;
        console.debug(`GAME is being initialized with: ${player1_username} && ${player1_color} | ${player2_username} && ${player2_color} | BOT && ${bot_color}`);

        // Initialize the games object
        games[game_id] = {
            users: [],
            playerColors: {
                [player1_username]: player1_color,
                [player2_username]: player2_color
            },
            gameColors: [player1_color, player2_color, bot_color],
            gameInitialized: false,
            numberOfMessages: 0,
            accusationMade: false,
            timeIsUp: false,
            isTheLastMessageBot: false,
        };

        console.log(`games[game_id] for ID ${game_id} is:`, games[game_id]);
        return games[game_id];  // Return the initialized game object
        
    } catch (error) {
        console.error('Error in initiateGame:', error);
        throw error;  // Re-throw to be caught by the calling function
    }
}

function updateGameStartTime(game_id) {

    return new Promise((resolve, reject) => {
        db.run(sql_update_start_time, [game_id], function (err) {
            if (err) {
                console.error('--- DB: Error updating start_time:', err.message);
                return reject(err);
            }
            console.log(`--- DB: Start time updated for game ID ${game_id}`);
            resolve(this.changes); // Return the number of rows affected
        });
    });
}
function updateGameEndTime(game_id) {
    return new Promise((resolve, reject) => {
        db.run(sql_update_end_time, [game_id], function (err) {
            if (err) {
                console.error('--- DB: Error updating end_time:', err.message);
                return reject(err);
            }
            console.log(`--- DB: End time updated for game ID ${game_id}`);
            resolve(this.changes); // Return the number of rows affected
        });
    });
}

// Add these helper functions at the top of your server.js
function generateSessionId() {
    return Math.random().toString(36).substring(2) + Date.now().toString(36);
}

// In-memory session store (will be cleared on server restart)
const activeSessions = new Map();

const cookieParser = require('cookie-parser');
app.use(cookieParser());

app.use(express.json());

app.use((req, res, next) => {
    console.log(`${req.method} ${req.url}`);
    next();
});

// Serve static files from the src directory
app.use('/static', express.static(path.join(__dirname, 'src')));

app.get('/', (req, res) => {
    res.sendFile(__dirname + '/index.html');
});

app.post('/submit-username', (req, res) => {
    const { username } = req.body;

    if (!username) {
        return res.json({ success: false, error: 'Username is required.' });
    }

    // // Check if username is already in an active session
    // for (let [_, session] of activeSessions) {
    //     if (session.username === username) {
    //         return res.json({ success: false, error: 'Username is already in use.' });
    //     }
    // }

    // Check if the username exists
    db.get(sql_check_username, [username], (err, row) => {
        if (err) {
            console.error('Error checking username:', err.message);
            return res.json({ success: false, error: 'Database error' });
        }

        const sessionId = generateSessionId();
        activeSessions.set(sessionId, { username });

        // Set cookie with proper settings
        res.cookie('sessionId', sessionId, { 
            maxAge: 24 * 60 * 60 * 1000, // 24 hours
            httpOnly: true,
            path: '/',
            sameSite: 'strict'
        });

        if (row.count > 0) {
            // Username exists - login successful
            console.log(`User ${username} logged in with session ${sessionId}`);
            return res.json({ success: true });
        }

        // Username doesn't exist - register new user
        db.run(sql_insert_username, [username, username], function(err) {
            if (err) {
                console.error('Error inserting username:', err.message);
                return res.json({ success: false, error: 'Database error during insertion' });
            }
            console.log(`New user ${username} registered with session ${sessionId}`);
            res.json({ success: true });
        });
    });
});

// Add some debug logging to see what's happening with sessions
app.get('/api/current-user', (req, res) => {
    const sessionId = req.cookies.sessionId;
    console.log('Current user check - Session ID:', sessionId);
    console.log('Active sessions:', Array.from(activeSessions.keys()));
    
    if (!sessionId || !activeSessions.has(sessionId)) {
        console.log('Session not found or invalid');
        return res.json({ error: 'Not logged in' });
    }
    const { username } = activeSessions.get(sessionId);
    console.log('Found username:', username);
    res.json({ username });
});

app.get('/game-entry', (req, res) => {
    const sessionId = req.cookies.sessionId;
    console.log('Game entry - Session ID:', sessionId);
    console.log('Active sessions:', Array.from(activeSessions.keys()));
    console.log('Cookie header:', req.headers.cookie); // Add this line

    if (!sessionId || !activeSessions.has(sessionId)) {
        console.log('Game entry - Invalid session, redirecting to root');
        return res.redirect('/');
    }
    console.log('Game entry - Valid session, serving game entry page');
    res.sendFile(__dirname + '/gameentry.html');
});

app.post('/logout', (req, res) => {
    const sessionId = req.cookies.sessionId;
    if (sessionId) {
        activeSessions.delete(sessionId);
        res.clearCookie('sessionId');
    }
    res.json({ success: true });
});

app.get('/game/:game_id', (req, res) => {
    const sessionId = req.cookies.sessionId;
    if (!sessionId || !activeSessions.has(sessionId)) {
        console.error('Game ID - Invalid session, redirecting to root');
        return res.redirect('/game-entry');
    }
    res.sendFile(__dirname + '/chatroom.html');
});

app.get('/api/user-games/:username', (req, res) => {
    const { username } = req.params;
    
    // Query to get user's games ordered by the 'order' field
    const sql = `
        SELECT game_id, player_order 
        FROM usersandgames 
        WHERE username = ? 
        ORDER BY player_order ASC
        LIMIT 10
    `;
    
    db.all(sql, [username], (err, rows) => {
        if (err) {
            console.error('Error fetching user games:', err);
            return res.status(500).json({ error: 'Database error' });
        }
        res.json(rows);
    });

    console.error(`res is: ${res}`);
});

// Check game status. Is completed?
app.get('/api/game-status/:gameId', (req, res) => {
    const { gameId } = req.params;
    const sql = `SELECT is_completed FROM games WHERE game_id = ?`;
    
    db.get(sql, [gameId], (err, row) => {
        if (err) {
            console.error('Error checking game status:', err);
            return res.status(500).json({ error: 'Database error' });
        }
        if (!row) {
            return res.status(404).json({ error: 'Game not found' });
        }
        res.json({ is_completed: row.is_completed });
    });
});

app.get('/api/leaderboard', (req, res) => {
    db.all(sql_get_leaderboard, [], (err, rows) => {
        if (err) {
            console.error('Error fetching leaderboard:', err);
            return res.status(500).json({ error: 'Database error' });
        }
        res.json(rows);
    });
});

// Add this middleware to Socket.IO connection
io.use((socket, next) => {
    const sessionId = socket.handshake.headers.cookie?.split(';')
        .find(c => c.trim().startsWith('sessionId='))
        ?.split('=')[1];
        
    if (!sessionId || !activeSessions.has(sessionId)) {
        return next(new Error('Authentication error'));
    }
    
    socket.username = activeSessions.get(sessionId).username;
    next();
});


function getCurrentTime() {
    const now = new Date();
    return now.toISOString().slice(0, 19).replace('T', ' '); // Format to 'YYYY-MM-DD HH:MM:SS'
}
// Helper function to get random time between 5-10 seconds
function getNextBotResponseTime() {
    return Math.floor(Math.random() * (10 - 8 + 1) + 8);
}
// Start the game timer when a new game begins
function gameTimer(game_id) {
    let remainingTime = gameDuration; // 5 minutes in seconds
    let nextBotResponseTime = remainingTime - Math.floor(Math.random() * (4 - 2 + 1) + 2); // Initial bot response time

    // Emit remaining time every second
    gameTimers[game_id] = setInterval(() => {
        if (remainingTime > 0) {
            remainingTime -= 1;

            // Check if it's time for bot to respond
            if (remainingTime <= nextBotResponseTime) {
                // Only try to send if the last message wasn't from the bot
                if (games[game_id] && !games[game_id].isTheLastMessageBot && chat_store[game_id].length > 0) {
                    sendChatHistoryToBot(game_id);
                }
                // Set next bot response time
                nextBotResponseTime = remainingTime - getNextBotResponseTime();
                console.log(`Game ${game_id}: Next bot response scheduled at ${nextBotResponseTime} seconds`);
            }

            io.to(`game_${game_id}`).emit('updateTimer', { remainingTime });
        } else {
            clearInterval(gameTimers[game_id]);
            delete gameTimers[game_id];
            delete botTimers[game_id];
            triggerAccusationPhase(game_id);
        }
    }, 1000);

    updateGameStartTime(game_id).catch(err => {
        console.error('--- DB: Failed to update start time:', err);
    });
}

// Trigger accusation phase when timer ends
function triggerAccusationPhase(game_id) {
    if(games[game_id] && !games[game_id].timeIsUp) {
        games[game_id].timeIsUp = true;
    }   
    io.to(`game_${game_id}`).emit('timeUpForAccusation', {
        message: "Time is up! You have 15 seconds to accuse someone."
    });

    // Start 15-second timer for final accusations
    setTimeout(() => {
        endGame(game_id);
    }, 15000);
}

// Handle socket connection and game room logic
io.on('connection', (socket) => {
    console.log('A user connected:', socket.id);

    // When the user joins a specific game room
    socket.on('joinGame', async ({ username, game_id }) => {
        users[socket.id] = username;
        console.log(`Player ${username} is trying to join the game ${game_id}`);
    
        try {
            if (!games[game_id]) {
                console.debug('# # # # 1 # # # # ');
                await initiateGame(username, game_id);
            } else {
                console.debug('# # # # 2 # # # # ');
                console.log(`-#-# Username ${username} returned to the game ${game_id}`);
            }

            if (!chat_store[game_id]) {
                chat_store[game_id] = [];
            }

            const game = games[game_id];
            if (!game) {
                throw new Error(`Game ${game_id} initialization failed`);
            }

            const assignedColor = game.playerColors[username];
            console.log(`${assignedColor} joined game ${game_id}`);
            socket.emit('colorAssigned', { color: assignedColor, username, game_id });
            if(game.users.length == 0 || (username != game.users[0].username && (game.users.length == 1 || (username != game.users[1].username)))) {
                game.users.push({ id: socket.id, username: username, color: assignedColor });
            }

            // Join the user to the game room
            socket.join(`game_${game_id}`);


            // Initialize the bot when 2 players have joined
            if (game.users.length === 2 && !game.gameInitialized) {
                console.log('There is only one user though...');
                initializeBot(game_id);
                game.gameInitialized = true;

                io.to(`game_${game_id}`).emit('message', {
                    color: 'Start', // Use a system color or identifier for such messages
                    message: 'The Game is starting now. You have 5 minutes to chat with each other.',
                    bold: 1
                });

                // Start the timer if this is a new game
                if (!gameTimers[game_id]) {
                    gameTimer(game_id);
                } else {
                    console.error('This game is supposed to be new but it is not. WHY?');
                }

            } else {
                io.to(`game_${game_id}`).emit('message', {
                    color: 'Warning', // Use a system color or identifier for such messages
                    message: 'The Game will start when your opponents join this chat room. Please wait patiently.',
                    bold: 1
                });
            }
            console.log('Current game state:', game_id, game);

            game.users.forEach(user => {
                // Get the user's assigned color
                const userColor = user.color;

                // Exclude the user's color from gameColors to get the other two colors
                const otherColors = game.gameColors.filter(color => color !== userColor);
                // Send the colors of the other two players to the client
                io.to(user.id).emit('otherPlayers', { otherPlayers: otherColors });
            });

            // Initialize accusation data for the game if not present
            if (!activeAccusations[game_id]) {
                activeAccusations[game_id] = { firstAccuser: null, secondAccuser: null };
            }
        } catch (error) {
            console.error('Error in joinGame:', error);
            socket.emit('error', {
                type: 'game_error',
                message: 'Failed to join game',
                details: error.message
            });
        }
    });

    // Handle message broadcasting within the room
    socket.on('sendMessage', ({ game_id, message, color }) => {
        if (!games[game_id]) {
            return console.error(`Game ID ${game_id} not found for the message ${message}`);
        }
        const game = games[game_id];
        const sent_time = getCurrentTime();
        if (!games[game_id].gameInitialized) {
            socket.emit('message', {
                color: 'system',
                message: 'The game has not started yet. Please wait until all players are present.',
                bold: 1
            });
            return;
        }
        if (games[game_id].accusationMade) {
            socket.emit('message', {
                color: 'system',
                message: 'The game is ending now. Please accuse someone.',
                bold: 1
            });
            return;
        }
        // Store the user's message in the chat history
        chat_store[game_id].push({
            role: "user",
            content: `${color}: ${message}`
        });
        games[game_id].isTheLastMessageBot = false;

        // Broadcast the user's message to the room
        io.to(`game_${game_id}`).emit('message', {
            color,
            message,
            bold: 0
        });

        // Add the message to the database:
        nextMessageId = game.numberOfMessages;
        db.run(sql_insert_messages,
            [game_id, nextMessageId, color, message, sent_time],
            (err) => {
                if (err) return console.error('--- DB: Error adding the message to the db:', err.message);
            });
        games[game_id].numberOfMessages += 1;
        console.log(`--- DB: message ${message} is added by the user ${color} in the game ${game_id} as the message number ${nextMessageId}`);
    });

    // Handle user disconnection
    socket.on('disconnect', () => {
        console.log('A user disconnected:', socket.id);
        username = users[socket.id];
        if (!username) {
            console.error(`ERROR: username is not defined inside the users dict...`);
        }
        Object.keys(games).forEach(game_id => {
            const game = games[game_id];
            // user_info = game.users.filter(user => user.id === socket.id);
            const userIndex = game.users.findIndex(user => user.id === socket.id);

            if (userIndex !== -1) { // Check if user is in the game
                const [user_info] = game.users.splice(userIndex, 1); // Remove user and store info
                leaveGame(game_id, user_info.color); // Pass the user's color to leaveGame
            }
            console.log('Current game state:', game_id, games[game_id]);
            // leaveGame(game_id, user_info.color);
        });
    });

    socket.on('accusePlayer', async ({ game_id, accuser, accused }) => {
        const game = games[game_id];
        if (!game) {
            console.error(`Game not found: ${game_id}`);
            return;
        }
        if (!game.gameInitialized) {
            socket.emit('message', {
                color: 'system',
                message: 'The game has not started yet. Please wait until all players are present.',
                bold: 1
            });
            return;
        }
        try {
            await updateAccusationTime(game_id, accuser, accused);
            games[game_id].accusationMade = true;
            // Record the first accusation
            if (activeAccusations[game_id] && !activeAccusations[game_id].firstAccuser) {
                activeAccusations[game_id].firstAccuser = { accuser, accused };
                // Find the opponent (other human player who is not the bot and not the accuser)
                const player = game.users.find(user => user.color === accuser);
                const opponent = game.users.find(user => user.color !== accuser && user.color !== game.botColor);
                if(player) {
                    if(games[game_id] && !games[game_id].timeIsUp) {
                        io.to(player.id).emit('promptAccusation', {
                            message: `Your opponent has 15 seconds to accuse someone. The game will end afterwards.`,
                        });
                    }
                } else {
                    console.error('Player ID could not found in accusation..');
                }
                if (opponent) {
                    // Notify the opponent to make an accusation within 15 seconds
                    if(games[game_id] && !games[game_id].timeIsUp) {
                        io.to(opponent.id).emit('promptAccusation', {
                            message: `Your opponent has made an accusation. You have 15 seconds to accuse someone.`,
                        });
                    }
                    // Set a 15-second timer to end the game if no second accusation
                    setTimeout(() => {
                        if (activeAccusations[game_id] && !activeAccusations[game_id].secondAccuser) {
                            endGame(game_id);
                        }
                    }, 15000);
                }
            } else if (!activeAccusations[game_id].secondAccuser) {
                // Record the second accusation
                activeAccusations[game_id].secondAccuser = { accuser, accused };
                await endGame(game_id); // End the game immediately if both players have accused
            }
        } catch (error) {
            console.error('Error in accusePlayer handler:', error);
            socket.emit('error', {
                type: 'accusation_error',
                message: 'An error occurred while processing your accusation',
                details: error.message
            });
        }
    });

    socket.on('leaveGame', async ({ game_id, color }) => {
        leaveGame(game_id, color);
    });

    socket.on('reportGame', ({ game_id, reporter }) => {
        if (!games[game_id].gameInitialized) {
            return;
        } 
        const game = games[game_id];
        if (!game) return;
    
        // Find the opponent
        const opponent = game.users.find(user => user.color !== reporter && user.color !== game.botColor);
        
        if (opponent) {
            // Notify opponent
            io.to(opponent.id).emit('gameReported', {
                message: `Your opponent has made a report. The game will end now.`
            });
        }
    
        // End the game immediately without accusations
        endGame(game_id, `${reporter} has reported an issue.`);
    });

});

function updateAccusationTime(game_id, accuserColor, accusedColor) {
    const game = games[game_id];
    if (!game.gameInitialized) {
        return;
    }

    return new Promise((resolve, reject) => {
        db.get(sql_get_game, [game_id], (err, row) => {
            if (err) {
                console.error('--- DB: Error fetching game data:', err.message);
                reject(err);
            }
            if (!row) {
                console.log(`No game found with game_id: ${game_id}`);
                reject(err);
            }
            const { player1_color, player2_color, bot_color } = row;
            const currentTime = getCurrentTime();
            console.log(`--- DB: ${accuserColor} accused ${accusedColor} in game ${game_id}`);
            // Logic to determine accusation and update accordingly
            console.log(`-#-# accuserColor: ${accuserColor}, player1_color: ${player1_color}, player2_color: ${player2_color}`);

            if (accuserColor === player1_color) {
                if (accusedColor === player2_color) {
                    // wrong accusation
                    db.run(sql_update_player1_accusation, [currentTime, 2, game_id], (err) => {
                        if (err) console.error('--- DB: Error updating player1 accused player2:', err.message);
                    });
                } else if (accusedColor === bot_color) {
                    // right accusation
                    db.run(sql_update_player1_accusation, [currentTime, 1, game_id], (err) => {
                        if (err) console.error('--- DB: Error updating player1 accused bot:', err.message);
                    });
                } else if (accusedColor !== '') {
                    // leaft the game without accusation - no update.
                    console.error(`accusedColor not found: `, accusedColor);
                }
                resolve();
            } else if (accuserColor === player2_color) {
                if (accusedColor === player1_color) {
                    // wrong accusation
                    db.run(sql_update_player2_accusation, [currentTime, 2, game_id], (err) => {
                        if (err) console.error('--- DB: Error updating player2 accused player1:', err.message);
                    });
                } else if (accusedColor === bot_color) {
                    // right accusation
                    db.run(sql_update_player2_accusation, [currentTime, 1, game_id], (err) => {
                        if (err) console.error('--- DB: Error updating player2 accused bot:', err.message);
                    });
                } else if (accusedColor !== '') {
                    // leaft the game without accusation - no update.
                    console.error(`accusedColor not found: `, accusedColor);
                }
                resolve();
            } else {
                console.error('--- DB: accuserColor does not match player1_color or player2_color.', accuserColor, player1_color, player2_color);
                reject(err)
            }
        });
    });

}

async function leaveGame(game_id, color) {

    if (!games[game_id].gameInitialized) {
        return;
    } 
    try {
        const game = games[game_id];
        if (!game) return;

        const accused = ""; // or "" - depending on what your updateAccusationTime function expects
        await updateAccusationTime(game_id, color, accused);
        games[game_id].accusationMade = true;

        if (activeAccusations[game_id] && !activeAccusations[game_id].firstAccuser) {
            activeAccusations[game_id].firstAccuser = { color, accused };

            // Find the opponent
            const opponent = game.users.find(user => user.color !== color && user.color !== game.botColor);
            if (opponent) {
                // Notify opponent
                io.to(opponent.id).emit('promptAccusation', {
                    message: `Your opponent has left the game. Now, you have 15 seconds to accuse someone.`
                });
        
                // Set a 15-second timer for opponent's accusation
                setTimeout(() => {
                    if (games[game_id] && activeAccusations[game_id] && !activeAccusations[game_id].secondAccuser) {
                        endGame(game_id);
                    }
                }, 15000);
            } else {
                endGame(game_id);
            }
        } else if (!activeAccusations[game_id].secondAccuser) {
            // Record the second accusation
            activeAccusations[game_id].secondAccuser = { color, accused };
            endGame(game_id); // End the game immediately if both players have accused
        }
    } catch (error) {
        console.error('Error in leaveGame handler:', error);
        endGame(game_id); // Fallback to end game if there's an error
    }

}

// Function to end the game and broadcast results
async function endGame(game_id, reason = null) {
    try {
        // Set the Game to COMPLETED.
        await new Promise((resolve, reject) => {
            const updateCompletionSQL = `UPDATE games SET is_completed = 1 WHERE game_id = ?`;
            db.run(updateCompletionSQL, [game_id], (err) => {
                if (err) {
                    console.error('Error updating game completion status:', err);
                    reject(err);
                }
                resolve();
            });
        });

        const gameData = await new Promise((resolve, reject) => {
            db.get(sql_get_game, [game_id], (err, row) => {
                if (err) {
                    console.error('--- DB: Error fetching game data:', err.message);
                    reject(err);
                }
                if (!row) {
                    console.log(`No game found with game_id: ${game_id}`);
                    reject(new Error('Game not found'));
                }
                resolve(row);
            });
        });

        const { player1_color, player2_color, player1_accused, player1_accusation_time, player2_accused, player2_accusation_time, bot_color } = gameData;
        console.log(`Player 1 ${player1_color} accused: ${player1_accused} and Player 2 ${player2_color} accused: ${player2_accused} `);

        // Player Scores:
        let player1_score = 0;
        let player2_score = 0;
        let bot_score = 0;

        let player1_accusation = 'no one';
        let player1_accusation_status = '⭕ No';
        let player2_accusation = 'no one';
        let player2_accusation_status = '⭕ No';

        if(player1_accusation_time === null && player2_accusation_time === null) {
            console.debug('Both players could not make accusation');
            bot_score = 10;
        } else if(player1_accusation_time === null) {
            // player2 made an accusation
            if (player2_accused == 1) {
                // they accues the bot.
                player2_score = 10;
                bot_score = 6;
            } else if (player2_accused == 2) {
                // they accues other player.
                bot_score = 10;
            }
        } else if(player2_accusation_time === null) {
            // player1 made an accusation
            if (player1_accused == 1) {
                // they accues the bot.
                player1_score = 10;
                bot_score = 6;
            } else if (player1_accused == 2) {
                // they accues other player.
                bot_score = 10;
            }
        } else if(player1_accusation_time < player2_accusation_time) {
            console.log('player1 accused first');
            if(player1_accused == 1 && player2_accused == 1) {
                // both correct accusation
                player1_score = 10;
                player2_score = 7;
                bot_score = 0;
            } else if(player1_accused == 1 && player2_accused == 2) {
                // only player1 correct accusation
                player1_score = 10;
                player2_score = 0;
                bot_score = 8;
            } else if(player1_accused == 2 && player2_accused == 1) {
                // only player2 correct accusation
                player1_score = 0;
                player2_score = 10;
                bot_score = 8;
            } else if(player1_accused == 2 && player2_accused == 2) {
                // both incorrect accusation
                player1_score = 0;
                player2_score = 0;
                bot_score = 10;
            } else {
                console.error(`WHY ARE WE HERE? player1_accused: ${player1_accused} and player2_accused : ${player2_accused}`)
            }
        } else if(player1_accusation_time > player2_accusation_time) {
            console.log('player2 accused first');
            if(player1_accused == 1 && player2_accused == 1) {
                // both correct accusation
                player1_score = 7;
                player2_score = 10;
                bot_score = 0;
            } else if(player1_accused == 1 && player2_accused == 2) {
                // only player1 correct accusation
                player1_score = 10;
                player2_score = 0;
                bot_score = 8;
            } else if(player1_accused == 2 && player2_accused == 1) {
                // only player2 correct accusation
                player1_score = 0;
                player2_score = 10;
                bot_score = 8;
            } else if(player1_accused == 2 && player2_accused == 2) {
                // both incorrect accusation
                player1_score = 0;
                player2_score = 0;
                bot_score = 10;
            } else {
                console.error(`WHY ARE WE HERE? player1_accused: ${player1_accused} and player2_accused : ${player2_accused}`)
            }
        } else if(player1_accusation_time === player2_accusation_time) { 
            console.log('Both players accused at the same time');
            if(player1_accused == 1 && player2_accused == 1) {
                // both correct accusation
                player1_score = 9;
                player2_score = 9;
                bot_score = 0;
            } else if(player1_accused == 1) {
                // only player1 correct
                player1_score = 10;
                player2_score = 0;
                bot_score = 8;
            } else if(player2_accused == 1) {
                // only player2 correct
                player1_score = 0;
                player2_score = 10;
                bot_score = 8;
            } else {
                // both wrong
                player1_score = 0;
                player2_score = 0;
                bot_score = 10;
            }
        } else{
            console.error(`WHY ARE WE HERE? player1_accusation_time: ${player1_accusation_time} and player2_accusation_time: ${player2_accusation_time}`);
        }

        // Player 1 Green accused: 1 and Player 2 Red accused: 0 
        if (player1_accused == 1) {
            // they accues the bot.
            player1_accusation = `${bot_color}`;
            player1_accusation_status = '✅ Correct';
            if(player1_score == 0) {
                player1_score = 5;
            }
        } else if (player1_accused == 2) {
            // they accues other player.
            player1_accusation = `${player2_color}`;
            player1_accusation_status = '❌ Incorrect';
        }
        if (player2_accused == 1) {
            // they accues the bot.
            player2_accusation = `${bot_color}`;
            player2_accusation_status = '✅ Correct';
            if(player2_score == 0) {
                player2_score = 5;
            }
        } else if (player2_accused == 2) {
            // they accues other player.
            player2_accusation = `${player1_color}`;
            player2_accusation_status = '❌ Incorrect';
        }

        console.debug(`The player scores are being saved to the DB: player1_score: ${player1_score}, player2_score: ${player2_score}, bot_score: ${bot_score}, game_id: ${game_id}`);
        await new Promise((resolve, reject) => {
            db.run(sql_update_player_scores, [player1_score, player2_score, bot_score, game_id], function (err) {
                if (err) {
                    console.error('--- DB: Error updating scores:', err.message);
                    return reject(err);
                }
                console.log(`--- DB: End time updated for game ID ${game_id}`);
                resolve(this.changes); // Return the number of rows affected
            });
        });

        const gameResult = {
            game_id: game_id,
            message: "Game Over",
            player1_color: player1_color,
            player2_color: player2_color,
            player1_accusation: player1_accusation,
            player1_accusation_status: player1_accusation_status,
            player1_score: player1_score,
            player2_accusation: player2_accusation,
            player2_accusation_status: player2_accusation_status,
            player2_score: player2_score, 
            bot_color: `${bot_color}`,
            bot_score: bot_score,
            reason: reason
        };
        console.log(`Game ${game_id} ends with the results ${gameResult}`);
        await updateGameEndTime(game_id);
        // Broadcast the game results to all players in the game room
        io.to(`game_${game_id}`).emit('gameEnded', gameResult);

        await new Promise((resolve, reject) => {
            const updateUserScores = async () => {
                try {
                    // Get usernames for the players
                    const sql_get_usernames = `
                        SELECT username FROM usersandgames 
                        WHERE game_id = ? 
                        ORDER BY player_order ASC 
                        LIMIT 2
                    `;
                    
                    db.all(sql_get_usernames, [game_id], async (err, rows) => {
                        if (err) {
                            reject(err);
                            return;
                        }
                        
                        if (rows.length !== 2) {
                            reject(new Error('Could not find both players'));
                            return;
                        }

                        const [player1_username, player2_username] = rows.map(row => row.username);

                        // Update scores for both players
                        await new Promise((resolve, reject) => {
                            db.serialize(() => {
                                db.run('BEGIN TRANSACTION');
                                
                                try {
                                    db.run(sql_update_user_score, [player1_score, player1_username, player1_username]);
                                    db.run(sql_update_user_score, [player2_score, player2_username, player2_username]);
                                    
                                    db.run('COMMIT', (err) => {
                                        if (err) {
                                            console.error('Error during commit:', err);
                                            db.run('ROLLBACK');
                                            reject(err);
                                        } else {
                                            resolve();
                                        }
                                    });
                                } catch (error) {
                                    console.error('Error during transaction:', error);
                                    db.run('ROLLBACK');
                                    reject(error);
                                }
                            });
                        });

                        resolve();
                    });
                } catch (error) {
                    reject(error);
                }
            };

            updateUserScores().catch(reject);
        });

        io.emit('gameCompleted', { gameId: game_id });
        // Clean up game state
        delete games[game_id];
        delete chat_store[game_id];
        delete activeAccusations[game_id];
        delete gameTimers[game_id];
        delete botTimers[game_id];
    } catch (error) {
        console.error('Error ending game:', error);
    }
}

// Helper function to split messages
function splitBotMessage(message) {
    // 30% chance to split the message
    if (Math.random() > 0.3) {
        return [message];
    }

    // Look for ". " pattern
    const dotParts = message.split('. ');
    if (dotParts.length > 1) {
        // Find a split point roughly in the middle
        let totalLength = message.length;
        let currentLength = 0;
        for (let i = 0; i < dotParts.length - 1; i++) {
            currentLength += dotParts[i].length + 2; // +2 for ". "
            if (currentLength >= totalLength / 2) {
                const firstPart = dotParts.slice(0, i + 1).join('. ') + '.';
                const secondPart = dotParts.slice(i + 1).join('. ');
                return [firstPart, secondPart];
            }
        }
    }

    // If no dots or message is long, split at a space near the middle
    if (message.length > 80) {
        const words = message.split(' ');
        let totalLength = message.length;
        let currentLength = 0;
        for (let i = 0; i < words.length - 1; i++) {
            currentLength += words[i].length + 1; // +1 for space
            if (currentLength >= totalLength / 2) {
                const firstPart = words.slice(0, i + 1).join(' ');
                const secondPart = words.slice(i + 1).join(' ');
                return [firstPart, secondPart];
            }
        }
    }

    return [message];
}


// Retry configuration
const RETRY_ATTEMPTS = 3;
const INITIAL_TIMEOUT = 8000; // 8 seconds
const MAX_TIMEOUT = 12000;    // 12 seconds

// Send chat history to the bot
async function sendChatHistoryToBot(game_id) {

    if (!games[game_id]) {
        return;
    }
    
    console.log('Sending chat history to the bot...');
    const chatHistory = chat_store[game_id];  // Get chat history for the current game

    try {
        const controller = new AbortController(); // For timeout handling
        const timeout = setTimeout(() => controller.abort(), 180000); // 120,000 ms timeout
    
        const response = await fetch('http://bot:8005/response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                game_id,
                chat_history: chatHistory,
            }),
            signal: controller.signal, // Attach the signal for aborting
        });
    
        clearTimeout(timeout); // Clear the timeout if the response is received in time
    
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.text();
        console.log('Success receiving a response from the bot:', data);
    
        let botMessage = data || ''; // Ensure botMessage is a string
        botMessage = botMessage.slice(0, 120); 
        const botColor = games[game_id].botColor;
        console.log(`# ${botColor}: ${botMessage}`);
    
        if (!botMessage) {
            return;
        }

        if(!games[game_id].isTheLastMessageBot || Math.random() > 0.9) {
            
            chat_store[game_id].push({
                role: "assistant",
                content: `${botColor}: ${botMessage}`,
            });
            games[game_id].isTheLastMessageBot = true;
    
            const game = games[game_id];
            const sent_time = getCurrentTime();
    
            // Add the message to the database:
            nextMessageId = game.numberOfMessages;
            await new Promise((resolve, reject) => {
                db.run(sql_insert_messages,
                    [game_id, nextMessageId, botColor, botMessage, sent_time],
                    (err) => {
                        if (err) {
                            console.error('--- DB: Error adding the message to the db:', err.message);
                            reject(err);
                        } else {
                            resolve();
                        }
                    });
            });

            games[game_id].numberOfMessages += 1;
            console.log(`--- DB: message ${botMessage} is added by the bot ${botColor} in the game ${game_id} as the message number ${nextMessageId}`);
            // Send the entire chat history to the bot
    
            io.to(`game_${game_id}`).emit('message', {
                color: botColor,
                message: botMessage,
                bold: 0
            });
        } else {
            console.log(`Bot cannot send multiple messages bback to back. Message emitted: ${botMessage}`);
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            console.error('BOT ERROR - Request timed out after 120 seconds.');
        } else if (error.message.includes('ECONNREFUSED')) {
            console.error('BOT ERROR - Unable to connect to the bot server on port 8005. Please check the server status:', error);
        } else {
            console.error('BOT ERROR - Error sending chat history to bot:', error);
        }
        return;
    }

}


// Function to initialize the bot and assign its color
async function initializeBot(game_id) {
    const game = games[game_id];
    const player1Color = game.gameColors[0];
    const player2Color = game.gameColors[1];
    const botColor = game.gameColors[2];
    games[game_id].botColor = botColor;
    console.log(`Initializing the game ${game_id} with bot color ${botColor}`);

    console.log(`Sending the game initialization to bot: ${player1Color} && ${player2Color}`);

    try {
        const response = await fetch('http://bot:8005/start-game', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                game_id: game_id,
                botColor: botColor,
                player1Color: player1Color,
                player2Color: player2Color
            }),
        });
    
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
    
        console.log("Game initialized successfully.");
    } catch (error) {
        console.error("Error initializing game:", error.message);
    }

}

// Initialize tables and start the server only when they are ready
createUsernamesTable((err) => {
    console.log('username tables');
    createGamesTable((err) => {
        console.log('games tables');
        if (err) return console.error("Failed to create games table. Exiting.");
        createUsersandGamesTable((err) => {
            console.log('usersandgames tables');
            if (err) return console.error("Failed to create usersandgames table. Exiting.");
            createMessagesTable((err) => {
                console.log('messages tables');
                if (err) return console.error("Failed to create messages table. Exiting.");
                // Start the server only after tables are successfully created
                server.listen(PORT, '0.0.0.0', () => {
                    console.log(`Server is running on port ${PORT}`);
                });
            });
        })
    });
});