import { BehaviorSubject } from 'rxjs';
import { UUID } from 'molstar/lib/mol-util';


/** Restricts SubjectBehavior.next method to a specific session, 
 * so that async functions from the previous sessions cannot 
 * change state in the current session. */
export class SubjectSessionManager {
    currentSession: UUID = UUID.createv4();
    subjects: BehaviorSubjectWithinSession<any>[] = [];

    startNewSession() {
        this.currentSession = UUID.createv4();
        return this.currentSession;
    }
    behaviorSubject<T>(value: T) {
        const subject = new BehaviorSubjectWithinSession(value, this);
        this.subjects.push(subject);
        return subject;
    }
    resetAllSubjects() {
        for (const subject of this.subjects) {
            subject.reset();
        }
    }
}


class BehaviorSubjectWithinSession<T> extends BehaviorSubject<T> {
    readonly sessionManager: SubjectSessionManager;
    readonly default: T;

    constructor(value: T, sessionManager: SubjectSessionManager) {
        super(value);
        this.sessionManager = sessionManager;
        this.default = value;
    }
    /** Use `nextWithinSession` instead! */
    next(value: T) {
        console.error('Calling BehaviorSubjectWithinSession.next is not recommended. Call BehaviorSubjectWithinSession.nextWithinSession instead.');
        super.next(value);
    }
    nextWithinSession(value: T, session: UUID) {
        if (session === this.sessionManager.currentSession) {
            super.next(value);
        }
    }
    reset() {
        super.next(this.default);
    }
}
