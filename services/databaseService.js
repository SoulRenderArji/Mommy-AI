import { JSONFile } from 'lowdb/node';
import { Low } from 'lowdb';

const db = new Low(new JSONFile('db.json'), {});

async function initializeDatabase() {
    await db.read();
    db.data = db.data || {};
    db.data.users = db.data.users || {};
    db.data.memories = db.data.memories || [];
    db.data.journal = db.data.journal || [];
    db.data.firewall = db.data.firewall || { blocked_ips: [] };
    await db.write();
}

// ... (rest of the code)

export { 
    db, 
    initializeDatabase, 
    getCoreMemories,
    getChatHistory,
    getJournal,
    getFirewallRules, 
    setFirewallRule, 
    removeFirewallRule 
};