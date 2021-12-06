const express = require('express');
const app = express();
const random = require('random');

app.use(express.json());

// Max Number of Requests with the Same IP Address
const MAX_REQUESTS = 6;

const get_user_ip = async (request) => {
    const ip = await request.headers['x-forwarded-for'] || request.connection.remoteAddress;
    return ip.split(':')[3];
    //return 'test';
}

const check_user = async (email) => {
    var exists = false;

    await users.map(user => {
        if(email == user.email) exists = true;
    })

    return exists;
}

const check_ip_blacklisted = async (user_ip) => {
    var exists = false;

    await blacklist_ips.map(ip => {
        if(user_ip === ip.ip && ip.num_of_reqs >= MAX_REQUESTS) exists = true;
    })

    return exists;
}

const check_ip_already_requested = async (user_ip) => {
    var exists = false;

    await blacklist_ips.map(ip => {
        if(user_ip == ip.ip) exists = true;
    })

    return exists;
}

const handle_ip = async (user_ip) => {
    var requested = await check_ip_already_requested(user_ip)
    
    if(requested){
        blacklist_ips.map(ip => {
            if(ip.ip == user_ip) {
                ip.num_of_reqs = ip.num_of_reqs + 1

                if(ip.num_of_reqs >= MAX_REQUESTS) ip.blocked = true;
            }
        })
    }

    else {
        blacklist_ips.push({
            "ip": user_ip,
            "num_of_reqs": 1,
            "blocked": false
        })
    }

}

app.listen(80, function() { console.log('Running at Port 3000'); })

var users = [{
    "name": "Admin",
    "email": "admin@admin.com",
    "password": "pytorxy",
    "email_code": 0000,
    "email_code_active": false,
    "isAdmin": true
}];

var blacklist_ips = [{
    "ip": "127.0.0.0",
    "num_of_reqs": 6,
    "blocked": true
}]

app.get('/', async (req, resp) => {
    const ip = await get_user_ip(req);
    console.log(ip);

    resp.send('200 OK');
})

//++++++++++ Login Functions ++++++++++
app.post('/login', async (req, resp) => {
    const { email, password } = req.body;

    var user_exists = await check_user(email);
    if(!user_exists) resp.send('Usuário Não Existe');

    else {
        users.map(user => {
            if(user.email == email) {
                if(user.password == password) {
                    resp.send('Usuário Logado com Sucesso!');
                }
                else {
                    resp.send('Usuário ou Senha Incorretos');
                }
            }
        })        

    }

})
//++++++++++++++++++++++++++++++++++++++

//++++++++++ Register Functions +++++++++
app.post('/register', async (req, resp) => {
    
    const { name, email, password } = req.body;

    var user_exists = await check_user(email);
    if(user_exists) resp.send('Usuário Já Cadastrado');

    else {
        users.push({ name, email, password, email_code: 0000, email_code_active: false, isAdmin: false });
        resp.send('200 OK');
    }
})
//++++++++++++++++++++++++++++++++++++

//+++++++++ Forgot Password Functions ++++++++++
app.post('/forgot-password', async (req, resp) => {
    const { email } = req.body;

    const exists = await check_user(email);
    
    if(!exists) resp.send('Usuário Não Existe');

    users.map(user => {
        if(user.email == email) {
            const email_code = random.int(1000, 9999);
            user.email_code = email_code;
            user.email_code_active = true;
            
            console.log('Código: ' + email_code);
        }
    })
 
    resp.send('O Código de Recuperação foi Enviado!');    
})

app.post('/email-code-verify', async (req, resp) => {
    const { email, email_code, password } = req.body;

    var user_ip = await get_user_ip(req);

    const exists = await check_user(email);
    
    if(!exists) resp.send('Usuário Não Existe');

    users.map( async(user) => {
        if(user.email == email) {
            if(!user.email_code_active) resp.send('Não Habilitado');

            else {
                var is_ip_blacklisted = await check_ip_blacklisted(user_ip);

                if(is_ip_blacklisted) resp.send('Rate Limit || IP: ' + user_ip);

                else {
                    
                    await handle_ip(user_ip);

                    if(user.email_code == email_code){
                        user.password = password;
                        user.email_code_active = false;
                        resp.send('Senha atualizada com sucesso!');
                    }
    
                    else resp.send('Código Incorreto!');

                }

            }
        }
    })


})
//++++++++++++++++++++++++++++++++++++++++++++++

app.get('/users', async (req, resp) => {
    resp.send(users);
})

app.get('/blacklist', async (req, resp) => {
    resp.send(blacklist_ips);
})
