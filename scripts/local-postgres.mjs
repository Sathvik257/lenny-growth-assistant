import EmbeddedPostgres from 'embedded-postgres';
import { existsSync } from 'node:fs';
const pg = new EmbeddedPostgres({
 databaseDir: '.runtime/postgres', user: 'lenny', password: 'lenny_local_only',
 port: 54329, persistent: true, authMethod: 'scram-sha-256',
 initdbFlags: ['--encoding=UTF8', '--locale=C'],
 postgresFlags: ['-h', '127.0.0.1'],
 onLog: () => {}, onError: (m) => console.error(String(m)),
});
if (!existsSync('.runtime/postgres/PG_VERSION')) await pg.initialise();
await pg.start();
const client = pg.getPgClient();
await client.connect();
const result = await client.query("SELECT 1 FROM pg_database WHERE datname = 'lenny'");
await client.end();
if (!result.rowCount) await pg.createDatabase('lenny');
console.log('PostgreSQL ready on 127.0.0.1:54329');
let stopping = false;
async function stop() { if (stopping) return; stopping = true; await pg.stop(); process.exit(0); }
process.on('SIGINT', stop); process.on('SIGTERM', stop);
setInterval(() => {}, 60000);
