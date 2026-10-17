(function () {
    const dataElement = document.getElementById('skill-spend-data');
    const form = document.getElementById('skill-spend-form');
    if (!dataElement || !form) {
        return;
    }

    const config = JSON.parse(dataElement.textContent);
    const skills = config.skills;
    const byId = new Map(skills.map((skill) => [skill.id, skill]));
    const ranks = new Map();

    skills.forEach((skill) => {
        const input = document.getElementById('rank-' + skill.id);
        ranks.set(skill.id, input ? Number(input.value) || 0 : skill.owned);
    });
    const originalRanks = new Map(ranks);
    const originalText = new Map();
    form.querySelectorAll('tr[data-skill-id]').forEach((row) => {
        const skillId = row.dataset.skillId;
        const description = row.querySelector('.skill-description');
        const cost = row.querySelector('.skill-cost');
        if (description) {
            originalText.set('desc-' + skillId, description.textContent);
        }
        if (cost) {
            originalText.set('cost-' + skillId, cost.textContent);
        }
    });

    form.addEventListener('click', (event) => {
        const button = event.target.closest('button[data-action]');
        if (!button || button.disabled) {
            return;
        }
        const row = button.closest('tr[data-skill-id]');
        if (!row) {
            return;
        }
        const skillId = Number(row.dataset.skillId);
        const delta = button.dataset.action === 'increase' ? 1 : -1;
        changeRank(skillId, delta);
    });

    form.addEventListener('submit', () => {
        form.querySelectorAll('.skill-spend-submit').forEach((button) => {
            button.disabled = true;
        });
    });

    render();

    function changeRank(skillId, delta) {
        const skill = byId.get(skillId);
        if (!skill) {
            return;
        }
        const next = (ranks.get(skillId) || 0) + delta;
        if (next < 0) {
            return;
        }
        const limit = effectiveLimit(skill);
        if (limit !== null && next > limit) {
            return;
        }
        if (delta > 0 && increaseReason(skill)) {
            return;
        }
        if (delta < 0 && decreaseReason(skill)) {
            return;
        }
        ranks.set(skillId, next);
        const input = document.getElementById('rank-' + skillId);
        if (input) {
            input.value = String(next);
        }
        render();
    }

    function render() {
        const totals = pointTotals();
        skills.forEach((skill) => {
            const rank = ranks.get(skill.id) || 0;
            const row = form.querySelector('tr[data-skill-id="' + skill.id + '"]');
            if (!row) {
                return;
            }
            row.classList.toggle('skill-row-changed', rank !== originalRanks.get(skill.id));
            const rankLabel = row.querySelector('.skill-rank');
            if (rankLabel) {
                rankLabel.textContent = String(rank);
            }
            const unchanged = rank === originalRanks.get(skill.id);
            const costCell = row.querySelector('.skill-cost');
            if (costCell) {
                costCell.textContent = unchanged
                    ? originalText.get('cost-' + skill.id)
                    : nextCost(skill, rank) + ' CP';
            }
            const description = row.querySelector('.skill-description');
            if (description) {
                description.textContent = unchanged
                    ? originalText.get('desc-' + skill.id)
                    : (rank > 0
                        ? formatRankDescription(skill.description, rank, false)
                        : formatRankDescription(skill.description, 1, true));
            }
            row.querySelectorAll('button[data-action]').forEach((button) => {
                const increasing = button.dataset.action === 'increase';
                const reason = increasing ? increaseReason(skill) : decreaseReason(skill);
                button.disabled = Boolean(reason);
                if (reason && reason !== 'unavailable') {
                    button.title = reason;
                } else {
                    button.removeAttribute('title');
                }
                if (!skill.multiple) {
                    button.hidden = increasing ? rank > 0 : rank === 0;
                }
            });
        });

        setPoints('available-cp-value', totals.available);
        setPoints('available-cp-bar', totals.available);
        setPoints('spent-cp-value', totals.spent);

        const dirty = skills.some((skill) => (ranks.get(skill.id) || 0) !== originalRanks.get(skill.id));
        const status = document.getElementById('skill-spend-status');
        if (status) {
            status.hidden = !dirty;
        }
        form.querySelectorAll('.skill-spend-submit').forEach((button) => {
            button.disabled = !dirty;
        });
    }

    function setPoints(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = formatPoints(value);
        }
    }

    function increaseReason(skill) {
        const rank = ranks.get(skill.id) || 0;
        if (skill.requiredSkillId && rankOf(skill.requiredSkillId) <= 0) {
            return 'Requires ' + (skill.requiredSkillName || 'another skill');
        }
        const requirement = requirementError(skill);
        if (requirement) {
            return requirement;
        }
        const limit = effectiveLimit(skill);
        if (limit !== null && rank >= limit) {
            return 'Maximum ' + limit + ' ranks';
        }
        if (!canAfford(skill)) {
            return skill.earnedOnly ? 'Needs earned character points' : 'unavailable';
        }
        return '';
    }

    function decreaseReason(skill) {
        if ((ranks.get(skill.id) || 0) <= 0 || !config.canRefund) {
            return 'unavailable';
        }
        const owned = ownedIds();
        if (!owned.has(skill.id)) {
            return 'unavailable';
        }
        for (const peer of skills) {
            if (peer.id === skill.id || rankOf(peer.id) <= 0) {
                continue;
            }
            if (peer.requiredSkillId === skill.id) {
                return 'Cannot refund ' + skill.name + ' as it is required for ' + peer.name + '.';
            }
            if (peer.requiredAny.indexOf(skill.id) !== -1) {
                const stillHeld = peer.requiredAny.some((id) => id !== skill.id && owned.has(id));
                if (!stillHeld) {
                    return 'Cannot refund ' + skill.name + ' as it is required for ' + peer.name + '.';
                }
            }
            if (!peer.distinct.length || peer.distinct.indexOf(skill.id) === -1) {
                continue;
            }
            const key = poolKey(peer.distinct);
            const consumers = skills.filter((other) => owned.has(other.id) && poolKey(other.distinct) === key).length;
            const remaining = peer.distinct.filter((id) => owned.has(id)).length - 1;
            if (remaining < consumers) {
                return 'Cannot refund ' + skill.name + ' as it is required for ' + peer.name + '.';
            }
        }
        return '';
    }

    function requirementError(skill) {
        const owned = ownedIds();
        if (skill.requiredAny.length && !skill.requiredAny.some((id) => owned.has(id))) {
            return 'Requires one of ' + skill.requiredAnyNames;
        }
        if (skill.distinct.length && !hasDistinct(skill, owned)) {
            return 'Requires a different one of ' + skill.distinctNames;
        }
        return '';
    }

    function hasDistinct(skill, owned) {
        const key = poolKey(skill.distinct);
        let consumers = 0;
        skills.forEach((peer) => {
            if (!peer.distinct.length || poolKey(peer.distinct) !== key) {
                return;
            }
            if (owned.has(peer.id) || peer.id === skill.id) {
                consumers += 1;
            }
        });
        const poolOwned = skill.distinct.filter((id) => owned.has(id)).length;
        return poolOwned >= consumers;
    }

    function ownedIds() {
        const owned = new Set();
        skills.forEach((skill) => {
            if ((ranks.get(skill.id) || 0) > 0) {
                owned.add(skill.id);
            }
        });
        return owned;
    }

    function rankOf(skillId) {
        return ranks.has(skillId) ? ranks.get(skillId) || 0 : 0;
    }

    function poolKey(ids) {
        return ids.map(Number).slice().sort((left, right) => left - right).join(',');
    }

    function effectiveLimit(skill) {
        if (!skill.multiple) {
            return skill.rankLimit === null || skill.rankLimit === undefined
                ? 1
                : Math.min(1, skill.rankLimit);
        }
        return skill.rankLimit === null || skill.rankLimit === undefined ? null : skill.rankLimit;
    }

    function canAfford(skill) {
        return pointsFor(skill) + 1e-9 >= nextCost(skill, ranks.get(skill.id) || 0);
    }

    function pointsFor(skill) {
        const totals = pointTotals();
        if (skill.earnedOnly) {
            return totals.unspentEarned;
        }
        return totals.available;
    }

    function pointTotals() {
        let earnedOnly = 0;
        let other = 0;
        skills.forEach((skill) => {
            const cost = paidCost(skill, ranks.get(skill.id) || 0);
            if (skill.earnedOnly) {
                earnedOnly += cost;
            } else {
                other += cost;
            }
        });
        const earnedSpent = earnedOnly + Math.max(0, other - config.basePoints);
        const unspentBase = Math.max(0, config.basePoints - other);
        let unspentEarned;
        if (config.developing) {
            unspentEarned = Math.max(0, config.userPoints - earnedSpent);
        } else {
            const originalEarned = earnedSpentAt(originalRanks);
            unspentEarned = config.userPoints - (earnedSpent - originalEarned);
        }
        return {
            spent: earnedOnly + other,
            available: unspentEarned + unspentBase,
            unspentEarned: unspentEarned,
        };
    }

    function earnedSpentAt(rankMap) {
        let earnedOnly = 0;
        let other = 0;
        skills.forEach((skill) => {
            const cost = paidCost(skill, rankMap.get(skill.id) || 0);
            if (skill.earnedOnly) {
                earnedOnly += cost;
            } else {
                other += cost;
            }
        });
        return earnedOnly + Math.max(0, other - config.basePoints);
    }

    function adjustedFreeRanks(skill, timesPurchased) {
        const removed = Math.max(0, skill.owned - timesPurchased);
        const originalPaid = Math.max(0, skill.owned - skill.freeRanks);
        const freeRemoved = Math.max(0, removed - originalPaid);
        return Math.max(0, skill.freeRanks - freeRemoved);
    }

    function paidPurchases(skill, timesPurchased) {
        return Math.max(0, timesPurchased - adjustedFreeRanks(skill, timesPurchased));
    }

    function paidCost(skill, timesPurchased) {
        const paid = paidPurchases(skill, timesPurchased);
        if (skill.costIncreases) {
            let total = 0;
            for (let index = 0; index < paid; index += 1) {
                total += Math.max(0, skill.baseCost + index - skill.discount);
            }
            return total;
        }
        return Math.max(0, skill.baseCost - skill.discount) * paid;
    }

    function nextCost(skill, timesPurchased) {
        const paid = paidPurchases(skill, timesPurchased);
        let cost = skill.baseCost;
        if (skill.costIncreases) {
            cost += paid;
        }
        return Math.max(0, cost - skill.discount);
    }

    function formatPoints(value) {
        const rounded = Math.round(value * 1000) / 1000;
        if (Math.abs(rounded - Math.round(rounded)) < 1e-9) {
            return String(Math.round(rounded));
        }
        return String(rounded);
    }

    function formatRankDescription(description, count, perRank) {
        if (!description) {
            return '';
        }
        const rank = Number.parseInt(count, 10);
        if (Number.isNaN(rank)) {
            return description;
        }
        return description.replace(/\{([^{}]*)\}/g, (original, inner) => {
            const expression = inner.trim();
            if (!expression || expression.length > 200) {
                return original;
            }
            if (/^(?:rank|num)$/.test(expression)) {
                return String(rank);
            }
            const operation = /^(?:rank|num)\s*([*+/\-])\s*(\d+)$/.exec(expression);
            if (operation) {
                try {
                    const result = applyOperation(rank, operation[1], Number.parseInt(operation[2], 10));
                    return perRank ? '(' + result + '/rank)' : String(result);
                } catch (error) {
                    return original;
                }
            }
            try {
                return String(evaluateExpression(expression, rank));
            } catch (error) {
                return original;
            }
        });
    }

    function applyOperation(count, operator, operand) {
        if (operator === '*') {
            return count * operand;
        }
        if (operator === '+') {
            return count + operand;
        }
        if (operator === '-') {
            return count - operand;
        }
        if (operand === 0) {
            throw new Error('division by zero');
        }
        return Math.floor(count / operand);
    }

    function evaluateExpression(expression, count) {
        let index = 0;

        function skip() {
            while (expression[index] === ' ') {
                index += 1;
            }
        }

        function parseExpression() {
            let value = parseTerm();
            for (;;) {
                skip();
                const operator = expression[index];
                if (operator !== '+' && operator !== '-') {
                    break;
                }
                index += 1;
                const right = parseTerm();
                value = operator === '+' ? value + right : value - right;
            }
            return value;
        }

        function parseTerm() {
            let value = parseUnary();
            for (;;) {
                skip();
                const operator = expression[index];
                if (operator !== '*' && operator !== '/') {
                    break;
                }
                index += 1;
                if (operator === '/' && expression[index] === '/') {
                    index += 1;
                }
                const right = parseUnary();
                if (operator === '*') {
                    value *= right;
                } else if (right === 0) {
                    throw new Error('division by zero');
                } else {
                    value = Math.floor(value / right);
                }
            }
            return value;
        }

        function parseUnary() {
            skip();
            if (expression[index] === '+') {
                index += 1;
                return parseUnary();
            }
            if (expression[index] === '-') {
                index += 1;
                return -parseUnary();
            }
            return parsePrimary();
        }

        function parsePrimary() {
            skip();
            if (expression[index] === '(') {
                index += 1;
                const value = parseExpression();
                skip();
                if (expression[index] !== ')') {
                    throw new Error('expected parenthesis');
                }
                index += 1;
                return value;
            }
            if (/[0-9]/.test(expression[index] || '')) {
                const start = index;
                while (/[0-9]/.test(expression[index] || '')) {
                    index += 1;
                }
                return Number.parseInt(expression.slice(start, index), 10);
            }
            const rest = expression.slice(index);
            const name = /^(?:rank|num)(?![A-Za-z0-9_])/.exec(rest);
            if (!name) {
                throw new Error('unsupported expression');
            }
            index += name[0].length;
            return count;
        }

        const value = parseExpression();
        skip();
        if (index !== expression.length || !Number.isInteger(value)) {
            throw new Error('unsupported expression');
        }
        return value;
    }
})();
